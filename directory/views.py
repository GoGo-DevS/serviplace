from urllib.parse import quote

from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render

from leads.models import LeadEvent

from .models import Category, Commune, Provider


def provider_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categoria', '').strip()
    commune_slug = request.GET.get('comuna', 'maipu').strip() or 'maipu'

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

    providers = providers.order_by('-is_featured', '-is_verified', 'business_name')

    categories = Category.objects.filter(is_active=True)
    communes = Commune.objects.filter(is_active=True)
    selected_category = categories.filter(slug=category_slug).first() if category_slug else None
    selected_commune = communes.filter(slug=commune_slug).first() if commune_slug else None

    title_tail = selected_category.name if selected_category else 'servicios'
    commune_name = selected_commune.name if selected_commune else 'Maipú'

    context = {
        'providers': providers,
        'categories': categories,
        'communes': communes,
        'query': query,
        'selected_category': selected_category,
        'selected_commune': selected_commune,
        'page_title': f'{title_tail} en {commune_name} | SERVIPLACE Maipú',
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
        'og_title': f'{provider.business_name} en SERVIPLACE Maipú',
        'og_description': provider.short_description,
    }
    return render(request, 'directory/provider_detail.html', context)


def whatsapp_redirect(request, slug):
    provider = get_object_or_404(Provider, slug=slug, is_active=True)
    Provider.objects.filter(pk=provider.pk).update(whatsapp_clicks_count=F('whatsapp_clicks_count') + 1)
    LeadEvent.objects.create(provider=provider, source_page='provider_detail', event_type=LeadEvent.WHATSAPP_CLICK)

    message = 'Hola, vi tu servicio en SERVIPLACE Maipú y necesito una cotización.'
    return redirect(f'https://wa.me/{provider.clean_whatsapp_number}?text={quote(message)}')

# Create your views here.
