from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db.models import Count, Prefetch, Q
from django.urls import reverse
from urllib.parse import urlencode
from django.utils import timezone

from directory.catalogo import categorias_por_grupo
from directory.models import Category, Commune, Provider, Region
from leads.models import LeadEvent
from directory import seo
from leads.registro import registrar


def home(request):
    ref_code = request.GET.get('ref', '')
    registrar(request, LeadEvent.PAGE_VIEW, origen='home')
    categories = Category.objects.filter(is_active=True)
    # Destacados = lo mejor del directorio, no lo primero que aparezca: solo
    # perfiles públicos (con dueño) Y con logo o foto. Mientras no haya
    # ninguno, la sección no se muestra (18-10-2026: se veían 12 importados
    # sin logo, marcados "Verificado" sin estarlo).
    featured_providers = (
        Provider.objects.publicos().exclude(foto='')
        .select_related('category', 'commune').distinct()
        .order_by('-is_featured', '-is_verified', 'business_name', 'pk')[:6]
    )
    publicos = Provider.objects.publicos()
    total_providers = publicos.count()
    communes_count = Commune.objects.filter(is_active=True, providers__in=publicos).distinct().count()
    regions_with_communes = Region.objects.filter(is_active=True).prefetch_related(
        Prefetch('communes', queryset=Commune.objects.filter(is_active=True).order_by('name'), to_attr='active_communes')
    ).order_by('name')

    context = {
        'categories': categories,
        'grupos': categorias_por_grupo(),
        'featured_providers': featured_providers,
        'total_providers': total_providers,
        'communes_count': communes_count,
        'regions_with_communes': regions_with_communes,
        'ref_code': ref_code,
        # El schema de la organización va SOLO acá (auditoría de Jorge): el
        # resto de las páginas la referencia por @id.
        'jsonld': seo.como_script(seo.organizacion_y_sitio()),
        'page_title': 'ServiPlace: maestros y profesionales en tu comuna',
        'meta_description': 'Gásfiter, electricista, kinesiólogo, psicólogo, profe particular y más en tu comuna. Contacto directo por WhatsApp, sin comisión.',
        'og_title': 'SERVIPLACE — Maestros y profesionales en tu comuna',
        'og_description': settings.SITE_DESCRIPTION,
    }
    return render(request, 'core/home.html', context)


def join(request):
    """`/sumate/` manda al flujo de autoservicio.

    05-09-2026 — Esta vista todavía usaba `ProviderApplicationForm`, el
    formulario de "postula y te contactamos para revisar antes de publicar".
    Ese flujo murió con el pivot Yapo (27-06): hoy cualquiera se registra y
    publica de inmediato desde `accounts`. El formulario ya no existía y la
    importación tumbaba el arranque entero del sitio.

    La URL se conserva porque está en el sitemap y en enlaces compartidos; el
    `?ref=` del programa de referidos se pasa de largo para no perderlo.
    """
    destino = reverse('accounts:provider_create')
    ref = request.GET.get('ref', '')
    if ref:
        destino = f'{destino}?ref={ref}'
    return redirect(destino)


def robots_txt(request):
    """`/robots.txt`. Permite todo lo público y bloquea lo que no es contenido.

    05-09-2026 — `config/urls.py` ya la enrutaba y la vista no existía: la
    sesión autónoma paró a mitad de la fase SEO. Sin este archivo el sitio
    arranca igual, pero Google rastrea el panel de cuenta y el admin, y esas
    URLs no aportan nada al índice.

    Texto plano y sin plantilla a propósito: un robots.txt con HTML por
    accidente lo ignora todo rastreador.
    """
    lineas = [
        'User-agent: *',
        'Disallow: /cuenta/',
        'Disallow: /admin/',
        'Allow: /',
        '',
        f'Sitemap: {settings.SITE_URL}/sitemap.xml',
        '',
    ]
    from django.http import HttpResponse
    return HttpResponse('\n'.join(lineas), content_type='text/plain; charset=utf-8')


def para_profesionales(request):
    """`/profesionales/`: la puerta de entrada de los profesionales independientes.

    17-10-2026 — Nace de una conversación con una kinesióloga de Concepción:
    a quien recién se titula, LinkedIn y los portales de empleo lo ponen a
    competir por un contrato, pero si atiende por su cuenta lo que necesita
    son pacientes, alumnos o clientes que lo encuentren en su comuna. Esta
    página le habla a esa persona; el producto es el mismo directorio.
    """
    registrar(request, LeadEvent.PAGE_VIEW, origen='profesionales')
    grupos = categorias_por_grupo(solo_grupos=[
        Category.SALUD, Category.EDUCACION, Category.BELLEZA, Category.PROFESIONAL,
    ])
    return render(
        request,
        'core/para_profesionales.html',
        {
            'grupos': grupos,
            'anio_actual': timezone.localdate().year,
            'page_title': 'Para profesionales independientes y recién titulados | SERVIPLACE',
            'meta_description': (
                'Kinesiólogos, psicólogos, nutricionistas, profes particulares y más: crea tu perfil gratis, '
                'muestra tu título y recibe consultas de tu comuna directo en tu WhatsApp. Sin comisión.'
            ),
            'og_title': 'Tus primeros clientes empiezan con un perfil — SERVIPLACE',
            'og_description': 'Crea tu perfil profesional gratis y recibe consultas directo en tu WhatsApp.',
        },
    )


def about(request):
    return render(
        request,
        'core/about.html',
        {
            'page_title': 'Qué es ServiPlace | Directorio de maestros y profesionales',
            'meta_description': 'ServiPlace es un directorio chileno de maestros y profesionales independientes por comuna, hecho por GoGoDevS. Contacto directo por WhatsApp, sin comisión.',
        },
    )


MOTIVOS_CONTACTO = [
    ('publicar', 'Quiero publicar mi perfil', 'Te ayudamos a dejarlo listo.',
     'Hola, quiero publicar mi perfil en ServiPlace y tengo una duda.'),
    ('corregir', 'Corregir o reclamar un perfil', 'Si tu negocio aparece con datos que no son.',
     'Hola, quiero corregir o reclamar un perfil en ServiPlace.'),
    ('datos', 'Mis datos o borrar mi perfil', 'Ver, corregir o borrar lo que tenemos de ti.',
     'Hola, escribo por mis datos personales en ServiPlace.'),
    ('otro', 'Otra consulta', 'Ideas, prensa o reportar un problema.',
     'Hola, tengo una consulta sobre ServiPlace.'),
]


def contact(request):
    numero = settings.DEFAULT_CONTACT_WHATSAPP
    motivos = [
        {'clave': clave, 'titulo': titulo, 'detalle': detalle,
         'url': f'https://wa.me/{numero}?{urlencode({"text": texto})}'}
        for clave, titulo, detalle, texto in MOTIVOS_CONTACTO
    ] if numero else []
    return render(
        request,
        'core/contact.html',
        {
            'motivos': motivos,
            'page_title': 'Contacto | ServiPlace',
            'meta_description': 'Escríbenos por WhatsApp para publicar tu perfil, reclamar o corregir uno que ya aparece, o pedir que borremos tus datos.',
        },
    )


def privacy(request):
    return render(
        request,
        'core/privacy.html',
        {
            'page_title': 'Política de privacidad | ServiPlace',
            'meta_description': 'Qué datos usa ServiPlace, para qué, con quién se comparten y cómo pedir que los corrijamos o borremos. Incluye Google Analytics y el CV.',
        },
    )


def terms(request):
    return render(
        request,
        'core/terms.html',
        {
            'page_title': 'Términos de uso | ServiPlace',
            'meta_description': 'Términos de uso de ServiPlace: cómo funciona el directorio, qué es responsabilidad de cada perfil y cómo pedir una corrección o la baja.',
        },
    )


def trust_and_safety(request):
    return render(
        request,
        'core/trust_and_safety.html',
        {
            'page_title': 'Seguridad y confianza | ServiPlace',
            'meta_description': 'Recomendaciones antes de contratar a un maestro o profesional: pide cotización clara, revisa su formación y acuerda precio y alcance por escrito.',
            'og_title': 'Seguridad y confianza en SERVIPLACE',
            'og_description': 'SERVIPLACE es una vitrina local para contactar prestadores directamente por WhatsApp en todo Chile.',
        },
    )

