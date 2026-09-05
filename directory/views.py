from urllib.parse import quote

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from leads.models import LeadEvent

from .models import Category, Commune, Provider, Region

# Cuántos prestadores por página. 24 entra en 3 columnas en escritorio y en 2
# en tablet sin dejar una fila coja, y en el teléfono son ~6 pantallas de
# scroll en vez de 190.
PROVEEDORES_POR_PAGINA = 24


def provider_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categoria', '').strip()
    commune_slug = request.GET.get('comuna', '').strip()

    providers = Provider.objects.filter(is_active=True).select_related('category', 'commune')

    if query:
        providers = providers.filter(
            Q(business_name__icontains=query)
            | Q(contact_name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(sector__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        providers = providers.filter(category__slug=category_slug)

    if commune_slug:
        providers = providers.filter(commune__slug=commune_slug)

    # `pk` al final del orden a propósito: sin un criterio único de desempate,
    # dos prestadores con el mismo destacado/verificado/nombre pueden salir en
    # orden distinto en cada consulta, y al paginar eso hace que uno se repita
    # en la página 2 y otro no aparezca nunca. Es el defecto clásico de
    # paginar sobre un orden no determinista.
    providers = providers.order_by('-is_featured', '-is_verified', 'business_name', 'pk')

    # D1 — El listado se pagina. Medido el 05-09: los 361 prestadores en una
    # sola página daban 162.604 px de alto en un teléfono, o sea unas 190
    # pantallas de scroll, y el navegador pedía las 361 fotos de una.
    paginador = Paginator(providers, PROVEEDORES_POR_PAGINA)
    numero = request.GET.get('page')
    try:
        pagina = paginador.page(numero)
    except PageNotAnInteger:
        pagina = paginador.page(1)
    except EmptyPage:
        # Pedir la página 999 devuelve la última, no un 404: la URL puede
        # venir de un enlace viejo o de Google, y un error ahí se lee como
        # sitio roto.
        pagina = paginador.page(paginador.num_pages)

    categories = Category.objects.filter(is_active=True)
    active_communes_qs = Commune.objects.filter(is_active=True).order_by('name')
    regions_with_communes = Region.objects.filter(is_active=True).prefetch_related(
        Prefetch('communes', queryset=active_communes_qs, to_attr='active_communes')
    ).order_by('name')
    selected_category = categories.filter(slug=category_slug).first() if category_slug else None
    selected_commune = active_communes_qs.filter(slug=commune_slug).first() if commune_slug else None

    title_tail = selected_category.name if selected_category else 'Servicios'
    commune_name = selected_commune.name if selected_commune else 'Chile'

    context = {
        # `providers` es la PÁGINA, no el queryset entero: la plantilla itera
        # sobre esto y si acá fuera el queryset completo la paginación sería
        # decorativa — se dibujarían los controles y se seguirían pintando los
        # 361. `pagina` va aparte para los controles.
        'providers': pagina.object_list,
        'pagina': pagina,
        'total_resultados': paginador.count,
        'categories': categories,
        'regions_with_communes': regions_with_communes,
        'query': query,
        'selected_category': selected_category,
        'selected_commune': selected_commune,
        'commune_name': commune_name,
        'page_title': f'{title_tail} en {commune_name} | SERVIPLACE',
        'meta_description': f'Busca {title_tail.lower()} y prestadores confiables en {commune_name}.',
    }
    return render(request, 'directory/provider_list.html', context)


def provider_detail(request, slug):
    provider = get_object_or_404(
        Provider.objects.select_related('category', 'commune').prefetch_related('images'),
        slug=slug,
        is_active=True,
    )
    Provider.objects.filter(pk=provider.pk).update(views_count=F('views_count') + 1)
    LeadEvent.objects.create(provider=provider, source_page='provider_detail', event_type=LeadEvent.DETAIL_VIEW)
    provider.views_count += 1

    context = {
        'provider': provider,
        'cover_image': provider.images.filter(is_cover=True).first(),
        'page_title': f'{provider.business_name} | {provider.category.name} en {provider.commune.name}',
        'meta_description': provider.short_description,
        'og_title': f'{provider.business_name} en SERVIPLACE',
        'og_description': provider.short_description,
    }
    return render(request, 'directory/provider_detail.html', context)


def whatsapp_redirect(request, slug):
    provider = get_object_or_404(Provider.objects.select_related('commune'), slug=slug, is_active=True)
    Provider.objects.filter(pk=provider.pk).update(whatsapp_clicks_count=F('whatsapp_clicks_count') + 1)
    LeadEvent.objects.create(provider=provider, source_page='provider_detail', event_type=LeadEvent.WHATSAPP_CLICK)

    message = f'Hola, vi tu perfil en SERVIPLACE {provider.commune.name} y necesito una cotización.'
    return redirect(f'https://wa.me/{provider.clean_whatsapp_number}?text={quote(message)}')

# Create your views here.
