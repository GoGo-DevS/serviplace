from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from directory.models import Provider

from .forms import ProviderForm, RegisterForm
from .models import UserProfile


def register(request):
    ref_code = request.GET.get('ref', '')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.whatsapp = form.cleaned_data.get('whatsapp', '')
            if ref_code:
                referrer_profile = UserProfile.objects.filter(referral_code=ref_code.upper()).first()
                if referrer_profile and referrer_profile.user != user:
                    profile.referred_by = referrer_profile.user
            profile.save()
            login(request, user)
            messages.success(request, f'Bienvenido/a a SERVIPLACE, {user.username}.')
            return redirect('accounts:dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'ref_code': ref_code,
        'page_title': 'Crear cuenta | SERVIPLACE',
    })


@login_required
def dashboard(request):
    my_providers = Provider.objects.filter(owner=request.user, is_active=True).select_related('category', 'commune')
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(request, 'accounts/dashboard.html', {
        'my_providers': my_providers,
        'profile': profile,
        'page_title': 'Mi cuenta | SERVIPLACE',
    })


@login_required
def provider_create(request):
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.owner = request.user
            provider.data_status = Provider.AUTHORIZED
            provider.is_active = True
            provider.save()
            messages.success(request, f'Perfil de "{provider.business_name}" publicado exitosamente.')
            return redirect('accounts:dashboard')
    else:
        form = ProviderForm()

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'is_create': True,
        'page_title': 'Publicar servicio | SERVIPLACE',
    })


@login_required
def provider_edit(request, slug):
    provider = get_object_or_404(Provider, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = ProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('accounts:dashboard')
    else:
        form = ProviderForm(instance=provider)

    return render(request, 'accounts/provider_form.html', {
        'form': form,
        'provider': provider,
        'is_create': False,
        'page_title': f'Editar {provider.business_name} | SERVIPLACE',
    })


@login_required
def claim_profile(request, slug):
    provider = get_object_or_404(Provider, slug=slug, is_active=True)

    if provider.owner is not None:
        messages.error(request, 'Este perfil ya tiene dueño.')
        return redirect(provider.get_absolute_url())

    if request.method == 'POST':
        provider.owner = request.user
        provider.claimed_at = timezone.now()
        provider.data_status = Provider.AUTHORIZED
        provider.save()
        messages.success(
            request,
            f'Perfil de "{provider.business_name}" reclamado. Ahora puedes editarlo desde tu dashboard.',
        )
        return redirect('accounts:provider_edit', slug=provider.slug)

    return render(request, 'accounts/claim_profile.html', {
        'provider': provider,
        'page_title': f'Reclamar perfil de {provider.business_name} | SERVIPLACE',
    })


def hazte_verificado(request):
    wa_number = settings.DEFAULT_CONTACT_WHATSAPP
    wa_message = 'Hola, quiero verificar mi perfil en SERVIPLACE y obtener el badge de negocio verificado.'
    wa_url = f'https://wa.me/{wa_number}?text={wa_message.replace(" ", "%20")}'
    return render(request, 'accounts/hazte_verificado.html', {
        'wa_url': wa_url,
        'page_title': 'Hazte Verificado | SERVIPLACE',
        'meta_description': 'Obtén el badge de negocio verificado en SERVIPLACE y destaca sobre la competencia.',
    })
