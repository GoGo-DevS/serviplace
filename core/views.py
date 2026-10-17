from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from directory.catalogo import categorias_por_grupo
from directory.models import Category, Commune, Provider
from leads.models import LeadEvent
from leads.registro import registrar


def home(request):
    ref_code = request.GET.get('ref', '')
    registrar(request, LeadEvent.PAGE_VIEW, origen='home')
    categories = Category.objects.filter(is_active=True)
    featured_providers = (
        Provider.objects.filter(is_active=True)
        .select_related('category', 'commune')
        .order_by('-is_featured', '-is_verified', 'business_name')[:6]
    )
    total_providers = Provider.objects.filter(is_active=True).count()
    communes_count = Commune.objects.filter(is_active=True, providers__is_active=True).distinct().count()

    context = {
        'categories': categories,
        'grupos': categorias_por_grupo(),
        'featured_providers': featured_providers,
        'total_providers': total_providers,
        'communes_count': communes_count,
        'ref_code': ref_code,
        'page_title': 'SERVIPLACE | Maestros y profesionales en tu comuna — Contacto directo',
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
            'page_title': 'Sobre SERVIPLACE',
            'meta_description': 'SERVIPLACE conecta vecinos con prestadores locales en todo Chile de forma simple y directa.',
        },
    )


def contact(request):
    return render(
        request,
        'core/contact.html',
        {
            'page_title': 'Contacto | SERVIPLACE',
            'meta_description': 'Contacta al equipo de SERVIPLACE.',
            'join_url': reverse('core:join'),
        },
    )


def terms(request):
    return render(
        request,
        'core/terms.html',
        {
            'page_title': 'Términos de Uso | SERVIPLACE',
            'meta_description': 'Términos de uso de SERVIPLACE — directorio de servicios locales en Chile.',
        },
    )


def trust_and_safety(request):
    return render(
        request,
        'core/trust_and_safety.html',
        {
            'page_title': 'Seguridad y confianza | SERVIPLACE',
            'meta_description': 'Recomendaciones para contactar prestadores por SERVIPLACE de forma clara y responsable.',
            'og_title': 'Seguridad y confianza en SERVIPLACE',
            'og_description': 'SERVIPLACE es una vitrina local para contactar prestadores directamente por WhatsApp en todo Chile.',
        },
    )

