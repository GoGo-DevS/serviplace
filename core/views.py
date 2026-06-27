from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from directory.forms import ProviderApplicationForm
from directory.models import Category, Commune, Provider


def home(request):
    categories = Category.objects.filter(is_active=True)
    featured_providers = (
        Provider.objects.filter(is_active=True, commune__slug='maipu')
        .select_related('category', 'commune')
        .order_by('-is_featured', '-is_verified', 'business_name')[:6]
    )
    communes = Commune.objects.filter(is_active=True)

    context = {
        'categories': categories,
        'popular_categories': categories[:6],
        'communes': communes,
        'featured_providers': featured_providers,
        'page_title': 'SERVIPLACE Maipú | Servicios locales cerca de ti',
        'meta_description': 'Encuentra gasfitería, cerrajería, electricidad, limpieza, climatización y otros servicios locales en Maipú.',
        'og_title': 'Encuentra servicios locales cerca de ti en Maipú',
        'og_description': settings.SITE_DESCRIPTION,
    }
    return render(request, 'core/home.html', context)


def join(request):
    message = 'Hola, quiero sumar mi servicio a SERVIPLACE Maipú gratis.'
    whatsapp_url = f'https://wa.me/{settings.DEFAULT_CONTACT_WHATSAPP}?text={message.replace(" ", "%20")}'

    if request.method == 'POST':
        form = ProviderApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Recibimos tu postulación. Te contactaremos para revisar la información antes de publicar tu perfil.',
            )
            return redirect('core:join')
    else:
        form = ProviderApplicationForm()

    context = {
        'form': form,
        'whatsapp_url': whatsapp_url,
        'page_title': 'Súmate gratis a SERVIPLACE Maipú',
        'meta_description': 'Postula tu servicio local en SERVIPLACE Maipú y recibe contactos directos por WhatsApp cuando tu perfil esté aprobado.',
        'og_title': 'Ofrece tu servicio en Maipú',
        'og_description': 'Suma tu negocio local a SERVIPLACE Maipú.',
    }
    return render(request, 'core/join.html', context)


def about(request):
    return render(
        request,
        'core/about.html',
        {
            'page_title': 'Sobre SERVIPLACE Maipú',
            'meta_description': 'SERVIPLACE Maipú conecta vecinos con prestadores locales de forma simple y directa.',
        },
    )


def contact(request):
    return render(
        request,
        'core/contact.html',
        {
            'page_title': 'Contacto | SERVIPLACE Maipú',
            'meta_description': 'Contacta al equipo de SERVIPLACE Maipú.',
            'join_url': reverse('core:join'),
        },
    )


def trust_and_safety(request):
    return render(
        request,
        'core/trust_and_safety.html',
        {
            'page_title': 'Seguridad y confianza | SERVIPLACE Maipú',
            'meta_description': 'Recomendaciones para contactar prestadores por SERVIPLACE Maipú de forma clara y responsable.',
            'og_title': 'Seguridad y confianza en SERVIPLACE Maipú',
            'og_description': 'SERVIPLACE Maipú es una vitrina local para contactar prestadores directamente por WhatsApp.',
        },
    )

# Create your views here.
