from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.antispam import excede_limite_ip, ip_cliente
from directory.forms import ProviderReportForm
from directory.models import Provider, ProviderReport

from .forms import ProviderForm, RegisterForm
from .models import LoginAttempt, UserProfile


class LoginThrottledView(LoginView):
    """Login con freno de fuerza bruta: N fallos por IP en M minutos → se bloquea la ventana."""

    template_name = 'accounts/login.html'
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
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('bloqueado', False)
        ctx['page_title'] = 'Iniciar sesión | ServiPlace'
        ctx['ventana_minutos'] = settings.LOGIN_VENTANA_MINUTOS
        return ctx


def register(request):
    ref_code = request.GET.get('ref', '') or request.POST.get('ref', '')
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
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
            messages.success(request, f'Bienvenido/a a ServiPlace, {user.username}. Ya puedes publicar tu servicio.')
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('accounts:provider_create')
    else:
        form = RegisterForm()

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
    my_providers = Provider.objects.filter(owner=request.user).select_related('category', 'commune')
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    claims = ProviderReport.objects.filter(claimant=request.user, kind=ProviderReport.CLAIM).select_related('provider')
    total_views = sum(p.views_count for p in my_providers)
    total_clicks = sum(p.whatsapp_clicks_count for p in my_providers)

    return render(request, 'accounts/dashboard.html', {
        'my_providers': my_providers,
        'profile': profile,
        'claims': claims,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'page_title': 'Mi cuenta | ServiPlace',
        'robots': 'noindex',
    })


@login_required
def provider_create(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProviderForm(request.POST)
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
            if provider.spam_flag:
                messages.info(request, 'Recibimos tu perfil. Quedó en revisión y lo publicaremos apenas lo mire una persona.')
            else:
                messages.success(request, f'Listo: "{provider.business_name}" ya está publicado.')
            return redirect(provider.get_absolute_url() if provider.is_active else 'accounts:dashboard')
    else:
        form = ProviderForm()

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'is_create': True,
        'page_title': 'Publicar mi servicio gratis | ServiPlace',
        'robots': 'noindex',
    })


@login_required
def provider_edit(request, slug):
    provider = get_object_or_404(Provider, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = ProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect(provider.get_absolute_url() if provider.is_active else 'accounts:dashboard')
    else:
        form = ProviderForm(instance=provider)

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'provider': provider,
        'is_create': False,
        'page_title': f'Editar {provider.business_name} | ServiPlace',
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
    wa_message = 'Hola, quiero verificar mi perfil en ServiPlace.'
    wa_url = f'https://wa.me/{wa_number}?text={wa_message.replace(" ", "%20")}' if wa_number else ''
    return render(request, 'accounts/hazte_verificado.html', {
        'wa_url': wa_url,
        'page_title': 'Perfil Verificado | ServiPlace',
        'meta_description': 'Qué es el perfil verificado de ServiPlace, qué incluye y cómo se obtiene.',
    })
