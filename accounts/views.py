from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.antispam import excede_limite_ip, ip_cliente
from directory.forms import ProviderReportForm
from directory.models import Provider, ProviderReport
from leads.models import LeadEvent
from leads.registro import registrar

from .cv import ACEPTA, CVIlegible, extraer_texto, proponer_perfil
from .forms import LoginForm, ProviderForm, RegisterForm, formatear_telefono, MAX_FOTOS
from .models import LoginAttempt, UserProfile


class LoginThrottledView(LoginView):
    """Login con freno de fuerza bruta: N fallos por IP en M minutos → se bloquea la ventana."""

    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def _bloqueado(self):
        ip = ip_cliente(self.request)
        if not ip:
            return False
        desde = timezone.now() - timezone.timedelta(minutes=settings.LOGIN_VENTANA_MINUTOS)
        return LoginAttempt.objects.filter(ip=ip, created_at__gte=desde).count() >= settings.LOGIN_MAX_INTENTOS

    def post(self, request, *args, **kwargs):
        if self._bloqueado():
            form = self.get_form_class()(request)
            respuesta = self.render_to_response(self.get_context_data(form=form, bloqueado=True))
            respuesta.status_code = 429
            return respuesta
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = ip_cliente(self.request)
        if ip:
            LoginAttempt.objects.create(ip=ip, username=(form.data.get('username') or '')[:150])
            # Una IP solo sirve mientras dura la ventana del freno: a los 30
            # días se borra (lo dice la política de privacidad).
            LoginAttempt.objects.filter(created_at__lt=timezone.now() - timezone.timedelta(days=30)).delete()
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('bloqueado', False)
        ctx['page_title'] = 'Iniciar sesión | ServiPlace'
        ctx['robots'] = 'noindex'
        ctx['ventana_minutos'] = settings.LOGIN_VENTANA_MINUTOS
        return ctx


def register(request):
    ref_code = request.GET.get('ref', '') or request.POST.get('ref', '')
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        ip = ip_cliente(request)
        limite, minutos = settings.LIMITE_REGISTROS_POR_IP
        if excede_limite_ip(UserProfile, ip, limite, minutos):
            form.add_error(None, 'Demasiados registros desde esta conexión. Intenta más tarde.')
        elif form.is_valid():
            spam, motivos = form.evaluar_spam()
            user = form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.whatsapp = form.cleaned_data.get('whatsapp', '')
            profile.created_ip = ip
            profile.spam_flag = spam
            profile.spam_reasons = motivos
            if ref_code:
                referrer_profile = UserProfile.objects.filter(referral_code=ref_code.upper()).first()
                if referrer_profile and referrer_profile.user != user:
                    profile.referred_by = referrer_profile.user
            profile.save()
            login(request, user)
            registrar(request, LeadEvent.SIGNUP_DONE, origen='register')
            request.session['ga4_eventos'] = request.session.get('ga4_eventos', []) + ['sign_up']
            if form.cv_texto:
                _guardar_borrador_cv(request, form.cv_texto)
            elif form.cv_error:
                request.session['cv_error'] = f'Tu cuenta quedó creada, pero no pudimos leer tu CV. {form.cv_error}'
            messages.success(request, f'Bienvenido/a a ServiPlace, {user.username}. Ya puedes publicar tu servicio.')
            next_url = request.GET.get('next') or request.POST.get('next')
            # `startswith('/')` dejaba pasar `//sitio-ajeno.com`, que el
            # navegador lee como otro dominio: una redirección abierta justo
            # después de crear la cuenta, el momento en que más se confía.
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('accounts:provider_create')
    else:
        form = RegisterForm()
        registrar(request, LeadEvent.SIGNUP_STARTED, origen=request.GET.get('desde', 'register')[:40])

    return render(request, 'accounts/register.html', {
        'form': form,
        'ref_code': ref_code,
        'next': request.GET.get('next', ''),
        'page_title': 'Crear cuenta gratis | ServiPlace',
        'meta_description': 'Crea tu cuenta en ServiPlace y publica tu servicio gratis en tu comuna.',
        'robots': 'noindex',
    })


@login_required
def dashboard(request):
    my_providers = Provider.objects.filter(owner=request.user).select_related('category', 'commune').prefetch_related(
        'otras_categorias', 'images')  # images: la versión de la historia de Instagram las cuenta
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    claims = ProviderReport.objects.filter(claimant=request.user, kind=ProviderReport.CLAIM).select_related('provider')
    total_views = sum(p.views_count for p in my_providers)
    total_clicks = sum(p.whatsapp_clicks_count for p in my_providers)
    tiene_verificado = any(p.is_verified for p in my_providers)

    return render(request, 'accounts/dashboard.html', {
        'my_providers': my_providers,
        'profile': profile,
        'claims': claims,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'tiene_verificado': tiene_verificado,
        'page_title': 'Mi cuenta | ServiPlace',
        'robots': 'noindex',
    })


# ---- CV que llena el perfil (18-10-2026; ver accounts/cv.py) -------------

def _guardar_borrador_cv(request, texto):
    """Lo que se leyó del CV queda en la sesión hasta que publica. El texto
    completo del CV no se guarda: solo los campos que se le proponen."""
    request.session['cv_borrador'] = proponer_perfil(texto)
    request.session.pop('cv_error', None)
    request.session['ga4_eventos'] = request.session.get('ga4_eventos', []) + ['cv_leido']


def _marcar_desde_cv(form, borrador):
    """Los campos que llenó el CV se ven distintos, para revisarlos."""
    for nombre in borrador:
        if nombre in form.fields:
            widget = form.fields[nombre].widget
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} desde-cv".strip()


@login_required
@require_POST
def leer_cv(request):
    archivo = request.FILES.get('cv')
    try:
        if not archivo:
            raise CVIlegible('Elige el archivo de tu CV (PDF o Word).')
        _guardar_borrador_cv(request, extraer_texto(archivo))
    except CVIlegible as error:
        request.session['cv_error'] = str(error)
    return redirect('accounts:provider_create')


@login_required
def provider_create(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    borrador = request.session.get('cv_borrador') or {}
    if request.method == 'POST':
        form = ProviderForm(request.POST, request.FILES)
        ip = ip_cliente(request)
        limite, minutos = settings.LIMITE_PERFILES_POR_IP
        if excede_limite_ip(Provider, ip, limite, minutos):
            form.add_error(None, 'Demasiadas publicaciones desde esta conexión. Intenta más tarde.')
        elif form.is_valid():
            spam, motivos = form.evaluar_spam()
            provider = form.save(commit=False)
            provider.owner = request.user
            provider.data_status = Provider.AUTHORIZED
            provider.claimed_at = timezone.now()
            provider.created_ip = ip
            provider.source_name = 'autoservicio'
            # Se GUARDA aunque parezca spam: queda oculto con la marca hasta que alguien lo mire.
            provider.spam_flag = spam or profile.spam_flag
            provider.spam_reasons = motivos or ('cuenta_marcada' if profile.spam_flag else '')
            provider.is_active = not provider.spam_flag
            if provider.spam_flag:
                provider.hidden_at = timezone.now()
                provider.moderation_note = 'Retenido por el filtro antispam al publicar.'
            provider.save()
            form.save_m2m()  # los otros rubros: con commit=False no se guardan solos
            form.guardar_fotos(provider)
            request.session.pop('cv_borrador', None)
            if provider.is_active:
                request.session['ga4_eventos'] = request.session.get('ga4_eventos', []) + ['publicar_perfil']
                registrar(request, LeadEvent.PROFILE_PUBLISHED, origen='provider_create', provider=provider,
                          category_slug=provider.category.slug, commune_slug=provider.commune.slug,
                          group=provider.category.group)
            if provider.spam_flag:
                messages.info(request, 'Recibimos tu perfil. Quedó en revisión y lo publicaremos apenas lo mire una persona.')
            else:
                messages.success(request, f'Listo: "{provider.business_name}" ya está publicado. '
                                          'Último paso: confirma tu WhatsApp con el botón de tu perfil.')
            return redirect(provider.get_absolute_url() if provider.is_active else 'accounts:dashboard')
    else:
        inicial = dict(borrador)
        # El WhatsApp que dio al registrarse, si el CV no traía uno.
        if profile.whatsapp and 'whatsapp_number' not in inicial:
            inicial['whatsapp_number'] = formatear_telefono(profile.whatsapp)
            inicial.setdefault('phone', inicial['whatsapp_number'])
        form = ProviderForm(initial=inicial)
    _marcar_desde_cv(form, borrador)

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'is_create': True,
        'max_fotos': MAX_FOTOS,
        'cv_campos': [form.fields[n].label for n in form.fields if n in borrador],
        'cv_error': request.session.pop('cv_error', ''),
        'cv_acepta': ACEPTA,
        'page_title': 'Publicar mi servicio gratis | ServiPlace',
        'robots': 'noindex',
    })


@login_required
def provider_edit(request, slug):
    provider = get_object_or_404(Provider, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = ProviderForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            form.guardar_fotos(provider)
            messages.success(request, 'Perfil actualizado.')
            return redirect(provider.get_absolute_url() if provider.is_active else 'accounts:dashboard')
    else:
        form = ProviderForm(instance=provider)

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'provider': provider,
        'is_create': False,
        'max_fotos': MAX_FOTOS,
        'page_title': f'Editar {provider.business_name} | ServiPlace',
        'robots': 'noindex',
    })


@login_required
def comprobaciones(request):
    """Donde Diego da los sellos (30-10-2026). WhatsApp: el dueño manda desde
    su número un mensaje con su código al WhatsApp de ServiPlace; aquí se
    confirma después de ver en el chat que llegó desde ESE número. Salud y SEC:
    se revisan en el registro público, con el enlace a mano."""
    if not request.user.is_staff:
        raise Http404  # no se anuncia que existe
    campos = {'whatsapp': 'whatsapp_confirmado_en', 'salud': 'registro_salud_comprobado_en',
              'sec': 'licencia_sec_comprobada_en'}
    if request.method == 'POST':
        campo = campos.get(request.POST.get('sello', ''))
        provider = Provider.objects.filter(pk=request.POST.get('perfil', '0') or 0).first() \
            if (request.POST.get('perfil') or '').isdigit() else None
        if request.POST.get('accion') == 'publicar' and provider and provider.owner_id:
            # Una ficha retenida por el antispam (o apagada) que Diego revisó y
            # es de una persona real. Se publica y se le quita la marca a la cuenta.
            nota = f'{provider.moderation_note}\nPublicada a mano por {request.user.username} el {timezone.localdate():%d-%m-%Y}.'.strip()
            Provider.objects.filter(pk=provider.pk).update(is_active=True, spam_flag=False, hidden_at=None,
                                                           moderation_note=nota)
            UserProfile.objects.filter(user_id=provider.owner_id).update(spam_flag=False)
            messages.success(request, f'Publicada: {provider.business_name}.')
            return redirect('accounts:comprobaciones')
        if campo and provider:
            dar = request.POST.get('accion') != 'quitar'
            Provider.objects.filter(pk=provider.pk).update(**{campo: timezone.now() if dar else None})
            messages.success(request, f'{"Listo" if dar else "Quitado"}: {provider.business_name}.')
        return redirect('accounts:comprobaciones')

    publicos = Provider.objects.publicos().select_related('commune').order_by('-created_at')
    # 11-11-2026: Manitos Curiosas se registró, el 502 le cortó el guardado y no
    # aparecía en ninguna parte: esta página solo listaba fichas públicas. Aquí
    # sale quien se registró en los últimos 30 días y no tiene ficha pública:
    # sin ficha, con una a medias o retenida por el antispam.
    sin_ficha = (get_user_model().objects
                 .filter(date_joined__gte=timezone.now() - timezone.timedelta(days=30), is_staff=False)
                 .exclude(pk__in=Provider.objects.publicos().values('owner_id'))
                 .select_related('profile')
                 .prefetch_related('providers')
                 .order_by('-date_joined'))
    return render(request, 'accounts/comprobaciones.html', {
        'sin_ficha': [
            {'u': u, 'fichas': list(u.providers.all()),
             'wa': _wa_digitos(getattr(getattr(u, 'profile', None), 'whatsapp', ''))}
            for u in sin_ficha
        ],
        'texto_ayuda': ('Hola, soy Diego de ServiPlace. Vi que te registraste pero tu ficha no quedó '
                        'publicada. ¿Te ayudo a terminarla?'),
        'whatsapp': [
            {'p': p, 'numero': formatear_telefono(p.whatsapp_number)}
            for p in publicos.filter(whatsapp_confirmado_en__isnull=True)
        ],
        'salud': publicos.exclude(health_registry='').filter(registro_salud_comprobado_en__isnull=True),
        'sec': publicos.exclude(licencia_sec='').filter(licencia_sec_comprobada_en__isnull=True),
        'recientes': publicos.filter(
            Q(whatsapp_confirmado_en__isnull=False) | Q(registro_salud_comprobado_en__isnull=False)
            | Q(licencia_sec_comprobada_en__isnull=False)).order_by('-updated_at')[:20],
        'url_rnpi': 'https://rnpi.superdesalud.gob.cl/',
        'url_sec': 'https://www.chileatiende.gob.cl/fichas/67276-buscador-de-instaladores-electricos-y-de-gas-autorizados-por-la-sec',
        'page_title': 'Comprobaciones | ServiPlace',
        'robots': 'noindex',
    })


def _wa_digitos(numero):
    """'+56 9 1234 5678' o '912345678' -> '56912345678' (para wa.me). Vacío si no sirve."""
    digitos = ''.join(c for c in (numero or '') if c.isdigit())
    if len(digitos) == 9 and digitos.startswith('9'):
        digitos = '56' + digitos
    return digitos if len(digitos) == 11 and digitos.startswith('569') else ''


@login_required
def historias(request):
    """La historia de Instagram de cada ficha pública, en una sola página
    (03-11-2026). Diego las sube a @serviplace.cl una por cliente; cada una
    tiene su cuadro para compartir, descargar y copiar el link del sticker."""
    if not request.user.is_staff:
        raise Http404  # no se anuncia que existe
    fichas = (Provider.objects.publicos()
              .select_related('category', 'commune')
              .prefetch_related('otras_categorias', 'images')
              .order_by('-created_at'))
    return render(request, 'accounts/historias.html', {
        'fichas': fichas,
        'page_title': 'Historias | ServiPlace',
        'robots': 'noindex',
    })


@login_required
def claim_profile(request, slug):
    """
    Reclamar NO asigna el perfil al instante: cualquiera con cuenta podría quedarse con el
    teléfono de un negocio real. Se crea una solicitud que un moderador aprueba en un clic.
    """
    provider = get_object_or_404(Provider, slug=slug, is_active=True)

    if provider.owner is not None:
        messages.error(request, 'Este perfil ya tiene dueño.')
        return redirect(provider.get_absolute_url())

    pendiente = ProviderReport.objects.filter(
        provider=provider, claimant=request.user, kind=ProviderReport.CLAIM, resolved_at__isnull=True
    ).first()

    if request.method == 'POST' and not pendiente:
        form = ProviderReportForm(request.POST)
        ip = ip_cliente(request)
        limite, minutos = settings.LIMITE_REPORTES_POR_IP
        if excede_limite_ip(ProviderReport, ip, limite, minutos):
            form.add_error(None, 'Demasiadas solicitudes desde esta conexión. Intenta más tarde.')
        elif form.is_valid():
            spam, motivos = form.evaluar_spam()
            report = form.save(commit=False)
            report.provider = provider
            report.kind = ProviderReport.CLAIM
            report.claimant = request.user
            report.created_ip = ip
            report.spam_flag = spam
            report.spam_reasons = motivos
            report.save()
            messages.success(request, 'Recibimos tu solicitud. Te confirmamos por WhatsApp o correo apenas la revisemos.')
            return redirect('accounts:dashboard')
    else:
        form = ProviderReportForm(initial={
            'kind': ProviderReport.CLAIM,
            'reporter_name': request.user.get_full_name() or request.user.username,
            'reporter_contact': request.user.email,
            'message': f'Soy el dueño o representante de {provider.business_name}. Pueden confirmarlo escribiéndome al WhatsApp del perfil.',
        })

    return render(request, 'accounts/claim_profile.html', {
        'provider': provider,
        'form': form,
        'pendiente': pendiente,
        'page_title': f'Reclamar perfil de {provider.business_name} | ServiPlace',
        'robots': 'noindex',
    })


def hazte_verificado(request):
    wa_number = settings.DEFAULT_CONTACT_WHATSAPP
    # 02-11-2026: el mensaje decía solo "quiero verificar mi perfil" y Diego no
    # sabía de qué perfil se trataba (le pasó con el primero que se inscribió
    # solo). Si quien lo pide ya tiene perfil, el mensaje dice cuál es y lleva
    # su código: como llega desde su número, con ese mismo mensaje también se
    # le puede confirmar el WhatsApp en /cuenta/comprobaciones/.
    perfil = None
    if request.user.is_authenticated:
        perfil = Provider.objects.publicos().filter(owner=request.user).order_by('is_verified', '-created_at').first()
    if perfil:
        wa_message = f'Hola, quiero verificar mi perfil en ServiPlace: {perfil.business_name}, {settings.SITE_URL}{perfil.get_absolute_url()}'
        if perfil.whatsapp_codigo:
            wa_message += f' Código: {perfil.whatsapp_codigo}'
    else:
        wa_message = 'Hola, quiero verificar mi perfil en ServiPlace.'
    wa_url = f'https://wa.me/{wa_number}?{urlencode({"text": wa_message})}' if wa_number else ''
    return render(request, 'accounts/hazte_verificado.html', {
        'wa_url': wa_url,
        'perfil': perfil,
        'page_title': 'Perfil Verificado | ServiPlace',
        'meta_description': 'Qué es el perfil verificado de ServiPlace, qué incluye y cómo se obtiene.',
    })
