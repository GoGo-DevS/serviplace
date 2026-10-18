from urllib.parse import quote

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, F, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from leads.models import LeadEvent
from leads.registro import es_bot, registrar, sanear_busqueda

from core import guias

from . import seo
from .catalogo import categorias_por_grupo, grupos_de, perfiles_por_rubro
from .models import Category, Commune, Provider, ProviderImage, Region

# Cuántos prestadores por página. 24 entra en 3 columnas en escritorio y en 2
# en tablet sin dejar una fila coja, y en el teléfono son ~6 pantallas de
# scroll en vez de 190.
PROVEEDORES_POR_PAGINA = 24


def url_listado(categoria=None, grupo=None, comuna=None):
    """La URL limpia de un listado. Nada indexable vive detrás de ?parametro
    (auditoría de Jorge: cada combinación paramétrica es una URL distinta para
    Google y dispersa la autoridad en vez de concentrarla)."""
    rubro = categoria.slug if categoria else (Category.GROUP_SLUGS.get(grupo) if grupo else None)
    if rubro and comuna:
        return reverse('directory:listado_rubro_comuna', kwargs={'rubro': rubro, 'comuna': comuna.slug})
    if rubro:
        return reverse('directory:listado_rubro', kwargs={'rubro': rubro})
    if comuna:
        return reverse('directory:listado_comuna', kwargs={'comuna': comuna.slug})
    return reverse('directory:provider_list')


def _resolver_rubro(rubro):
    """(categoría, grupo) a partir del primer tramo de la URL, o 404."""
    categoria = Category.objects.filter(slug=rubro, is_active=True).first()
    if categoria:
        return categoria, None
    grupo = Category.GROUP_POR_SLUG.get(rubro)
    if grupo:
        return None, grupo
    raise Http404


def provider_list(request):
    """`/servicios/`: el directorio completo y la búsqueda por texto.

    Los filtros por parámetro (?categoria=, ?comuna=, ?grupo=) ya no se sirven
    acá: redirigen con 301 a su URL limpia. Así siguen funcionando los enlaces
    viejos y el formulario de filtros, sin que Google vea dos URLs por página.
    """
    query = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('categoria', '').strip()
    com_slug = request.GET.get('comuna', '').strip()
    grupo = request.GET.get('grupo', '').strip()
    grupo = Category.GROUP_POR_SLUG.get(grupo, grupo if grupo in dict(Category.GROUP_CHOICES) else '')
    categoria = Category.objects.filter(slug=cat_slug, is_active=True).first() if cat_slug else None
    comuna = Commune.objects.filter(slug=com_slug, is_active=True).first() if com_slug else None

    if not query and (categoria or comuna or grupo):
        destino = url_listado(categoria, None if categoria else grupo, comuna)
        if request.GET.get('page'):
            destino += f"?page={quote(request.GET['page'])}"
        return redirect(destino, permanent=True)

    return _listado(request, categoria=categoria, grupo=None if categoria else grupo, comuna=comuna, query=query)


def listado_rubro(request, rubro):
    categoria, grupo = _resolver_rubro(rubro)
    return _listado(request, categoria=categoria, grupo=grupo)


def listado_rubro_comuna(request, rubro, comuna):
    categoria, grupo = _resolver_rubro(rubro)
    comuna_obj = get_object_or_404(Commune, slug=comuna, is_active=True)
    return _listado(request, categoria=categoria, grupo=grupo, comuna=comuna_obj)


def listado_comuna(request, comuna):
    return _listado(request, comuna=get_object_or_404(Commune, slug=comuna, is_active=True))


def _textos(categoria, grupo, comuna, query, total):
    """h1, <title>, description e introducción. Una intención por página."""
    nombre_grupo = dict(Category.GROUP_CHOICES).get(grupo, '')
    plural = 'perfil' if total == 1 else 'perfiles'
    if query:
        h1 = f'Resultados para «{query}»'
        return h1, f'{h1} | ServiPlace', f'Perfiles de ServiPlace que coinciden con «{query}».', ''
    if categoria and comuna:
        h1 = f'{categoria.nombre_busqueda} en {comuna.name}'
        verbo = 'atiende' if total == 1 else 'atienden'
        if categoria.group == Category.TIENDAS:  # una tienda no tiene "formación"
            intro = (f'{total} {plural} de {categoria.name.lower()} en {comuna.name}. '
                     f'Revisa qué ofrece cada una, si despacha o tiene local, y escríbele directo por WhatsApp.')
            meta = (f'{total} {plural} de {categoria.nombre_busqueda.lower()} en {comuna.name}. '
                    f'Mira qué ofrece cada una y escríbeles directo por WhatsApp, sin comisión.')
        else:
            intro = (f'{total} {plural} de {categoria.name.lower()} que {verbo} en {comuna.name}. '
                     f'Revisa qué hace cada uno, cómo atiende y su formación, y escríbele directo por WhatsApp.')
            meta = (f'{total} {plural} de {categoria.nombre_busqueda.lower()} en {comuna.name}. '
                    f'Mira su formación y zona de atención y escríbeles directo por WhatsApp, sin comisión.')
        return h1, f'{h1} | ServiPlace', meta[:158], intro
    if categoria:
        h1 = f'{categoria.nombre_busqueda}: perfiles por comuna'
        meta = (f'Encuentra {categoria.nombre_busqueda.lower()} en tu comuna. {categoria.description} '
                f'Contacto directo por WhatsApp, sin comisión.')
        intro = f'{categoria.description} Elige tu comuna para ver quién atiende cerca de ti.'
        return h1, f'{categoria.nombre_busqueda} por comuna | ServiPlace', meta[:158], intro
    if grupo and comuna:
        h1 = f'{nombre_grupo} en {comuna.name}'
        meta = f'{nombre_grupo} en {comuna.name}: {total} {plural} con contacto directo por WhatsApp, sin comisión.'
        return h1, f'{h1} | ServiPlace', meta[:158], ''
    if grupo:
        h1 = nombre_grupo
        descripcion = next((d for clave, _, d in Category.GRUPOS if clave == grupo), '')
        meta = f'{nombre_grupo} en tu comuna. {descripcion} Contacto directo por WhatsApp, sin comisión.'
        return h1, f'{nombre_grupo} en tu comuna | ServiPlace', meta[:158], descripcion
    if comuna:
        h1 = f'Maestros y profesionales en {comuna.name}'
        meta = (f'{total} {plural} en {comuna.name}: gásfiter, electricista, kinesiólogo, profe particular y más. '
                f'Contacto directo por WhatsApp.')
        return h1, f'{h1} | ServiPlace', meta[:158], ''
    h1 = 'Maestros y profesionales en Chile'
    meta = ('Directorio de maestros y profesionales independientes por comuna: gásfiter, electricista, '
            'kinesiólogo, psicólogo y más. Contacto directo por WhatsApp.')
    return h1, 'Directorio de maestros y profesionales | ServiPlace', meta[:158], ''


def _listado(request, *, categoria=None, grupo=None, comuna=None, query=''):
    providers = Provider.objects.publicos().select_related('category', 'commune').prefetch_related(
        # La foto de portada de cada tarjeta, en una sola consulta (G-04)
        Prefetch('images', queryset=ProviderImage.objects.filter(is_cover=True), to_attr='portadas'),
        'otras_categorias')
    if query:
        providers = providers.filter(
            Q(business_name__icontains=query)
            | Q(contact_name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(sector__icontains=query)
            | Q(category__name__icontains=query)
            | Q(pk__in=Provider.otras_categorias.through.objects
                .filter(category__name__icontains=query).values('provider_id'))
            | Q(profession_title__icontains=query)
            | Q(institution__icontains=query)
        )
    # Principal u otro rubro: el maestro que también es gásfiter sale en Gasfitería.
    if categoria:
        providers = providers.del_rubro(categoria)
    elif grupo:
        providers = providers.del_grupo(grupo)
    if comuna:
        providers = providers.filter(commune=comuna)

    # `pk` al final: sin un desempate único, al paginar uno se repite en la
    # página 2 y otro no aparece nunca (orden no determinista en Postgres).
    providers = providers.order_by('-is_featured', '-is_verified', 'business_name', 'pk')

    # D1 — El listado se pagina (361 en una página eran 162.604 px en un teléfono).
    paginador = Paginator(providers, PROVEEDORES_POR_PAGINA)
    try:
        pagina = paginador.page(request.GET.get('page'))
    except PageNotAnInteger:
        pagina = paginador.page(1)
    except EmptyPage:
        # La página 999 devuelve la última, no un 404: puede venir de un enlace viejo.
        pagina = paginador.page(paginador.num_pages)

    # Embudo: buscar = filtro aplicado en la primera página. Se registra aunque
    # no haya resultados: esas búsquedas son la lista de captación.
    if (query or categoria or comuna or grupo) and not request.GET.get('page'):
        registrar(
            request, LeadEvent.SEARCH, origen='provider_list',
            category_slug=categoria.slug if categoria else '', commune_slug=comuna.slug if comuna else '',
            group=grupo or (categoria.group if categoria else ''), query=sanear_busqueda(query),
            results_count=paginador.count,
        )

    total = paginador.count
    ga4_busqueda = None
    if (query or categoria or comuna or grupo) and not request.GET.get('page'):
        ga4_busqueda = {
            'search_term': (query or (categoria.nombre_busqueda if categoria else '') or '')[:80],
            'categoria': categoria.slug if categoria else (grupo or ''),
            'comuna': comuna.slug if comuna else '',
            'resultados': total,
        }
    h1, titulo, meta, intro = _textos(categoria, grupo, comuna, query, total)
    path = url_listado(categoria, grupo, comuna)
    es_pagina_limpia = bool(categoria or grupo or comuna) and not query
    # Una categoría vacía es 404, no 200 (auditoría de Jorge): si responde 200,
    # Google la indexa y compite contra las que sí tienen perfiles.
    vacia = es_pagina_limpia and total == 0

    numero = pagina.number
    canonical = path + (f'?page={numero}' if numero > 1 else '')
    if numero > 1:
        titulo = titulo.replace(' | ServiPlace', f', página {numero} | ServiPlace')

    pasos = [('Inicio', '/'), ('Servicios', reverse('directory:provider_list'))]
    if categoria:
        pasos.append((categoria.nombre_busqueda, url_listado(categoria)))
    elif grupo:
        pasos.append((dict(Category.GROUP_CHOICES)[grupo], url_listado(grupo=grupo)))
    if comuna:
        pasos.append((comuna.name, path))

    publicos = Provider.objects.publicos()
    relacionados_comunas, relacionados_categorias = [], []
    if categoria:
        relacionados_comunas = list(
            publicos.del_rubro(categoria).exclude(commune=comuna)
            .values('commune__slug', 'commune__name').annotate(n=Count('id')).order_by('-n', 'commune__name')[:12]
        )
        for fila in relacionados_comunas:
            fila['url'] = reverse('directory:listado_rubro_comuna',
                                  kwargs={'rubro': categoria.slug, 'comuna': fila['commune__slug']})
    if comuna:
        conteo = perfiles_por_rubro(publicos.filter(commune=comuna))
        otras = Category.objects.filter(slug__in=conteo)
        if categoria:
            otras = otras.exclude(pk=categoria.pk)
        relacionados_categorias = sorted(
            ({'category__slug': c.slug, 'category__name': c.name, 'category__seo_nombre': c.seo_nombre,
              'n': conteo[c.slug]} for c in otras),
            key=lambda f: (-f['n'], f['category__name']),
        )[:12]
        for fila in relacionados_categorias:
            fila['url'] = reverse('directory:listado_rubro_comuna',
                                  kwargs={'rubro': fila['category__slug'], 'comuna': comuna.slug})

    active_communes_qs = Commune.objects.filter(is_active=True).order_by('name')
    context = {
        # `providers` es la PÁGINA, no el queryset entero (si no, la paginación
        # sería decorativa). `pagina` va aparte para los controles.
        'providers': pagina.object_list,
        'pagina': pagina,
        'total_resultados': total,
        'grupos': categorias_por_grupo(),
        # Grupos con perfiles en ESTA comuna (o en todo el país): el chip de un
        # grupo vacío enlazaba a un listado que responde 404 a propósito, y
        # eso eran enlaces internos rotos en cada listado (rastreo 18-10-2026).
        'grupos_con_perfiles': grupos_de(
            Provider.objects.publicos().filter(**({'commune': comuna} if comuna else {}))
        ),
        'selected_group': grupo or '',
        'selected_category': categoria,
        'selected_commune': comuna,
        'query': query,
        'regions_with_communes': Region.objects.filter(is_active=True).prefetch_related(
            Prefetch('communes', queryset=active_communes_qs, to_attr='active_communes')
        ).order_by('name'),
        'h1': h1,
        'intro': intro,
        'pasos': pasos,
        'url_comuna_todo': url_listado(comuna=comuna) if comuna else reverse('directory:provider_list'),
        'relacionados_comunas': relacionados_comunas,
        'relacionados_categorias': relacionados_categorias,
        # Guías de confianza del rubro (verificar registro de salud, licencia SEC)
        'guias_rubro': guias.para_rubro(categoria.slug) if categoria else [],
        'page_title': titulo,
        'meta_description': meta,
        'ga4_busqueda': ga4_busqueda,
        'canonical': settings.SITE_URL + (reverse('directory:provider_list') if query else canonical),
        # Búsqueda libre y páginas vacías: fuera del índice, pero se siguen sus enlaces.
        'robots': 'noindex, follow' if (query or vacia) else '',
        'jsonld': seo.como_script(
            seo.miga(pasos),
            None if (query or vacia) else seo.listado(h1, path, pagina.object_list, total),
        ),
    }
    return render(request, 'directory/provider_list.html', context, status=404 if vacia else 200)


def provider_detail(request, slug):
    provider = get_object_or_404(
        Provider.objects.publicos().select_related('category', 'commune__region').prefetch_related(
            'images', 'otras_categorias'),
        slug=slug,
    )
    # Un bot (Google, la vista previa de WhatsApp) no es una visita: no suma
    # al contador que ve el profesional en su panel ni al embudo.
    if not es_bot(request):
        Provider.objects.filter(pk=provider.pk).update(views_count=F('views_count') + 1)
        registrar(request, LeadEvent.DETAIL_VIEW, origen='provider_detail', provider=provider,
                  category_slug=provider.category.slug, commune_slug=provider.commune.slug,
                  group=provider.category.group)
        provider.views_count += 1

    # Al compartir la ficha por WhatsApp, la vista previa muestra su logo o
    # foto. En R2 la URL ya es absoluta; en disco local hay que completarla.
    og_image = provider.foto.url if provider.foto else ''
    if og_image.startswith('/'):
        og_image = request.build_absolute_uri(og_image)

    pasos = [
        ('Inicio', '/'),
        ('Servicios', reverse('directory:provider_list')),
        (provider.category.nombre_busqueda, url_listado(provider.category)),
        (provider.commune.name, url_listado(provider.category, comuna=provider.commune)),
        (provider.business_name, provider.get_absolute_url()),
    ]
    titulo = f'{provider.business_name}: {provider.category.nombre_busqueda} en {provider.commune.name}'
    context = {
        'provider': provider,
        'pasos': pasos,
        'jsonld': seo.como_script(seo.miga(pasos), seo.perfil(provider, request)),
        'cover_image': provider.images.filter(is_cover=True).first(),
        'guias_rubro': guias.para_rubro(provider.category.slug),
        # Los otros rubros enlazan a su listado en la comuna: él está ahí, así
        # que nunca es un listado vacío (404).
        'otros_rubros': [
            {'categoria': c, 'url': reverse('directory:listado_rubro_comuna',
                                            kwargs={'rubro': c.slug, 'comuna': provider.commune.slug})}
            for c in provider.rubros[1:]
        ],
        'page_title': f'{titulo} | ServiPlace',
        'meta_description': (provider.short_description + f' Atiende en {provider.commune.name}. Contacto directo por WhatsApp.')[:158],
        'og_title': f'{provider.business_name} en SERVIPLACE',
        'og_image': og_image,
        'og_description': provider.short_description,
    }
    return render(request, 'directory/provider_detail.html', context)


def whatsapp_redirect(request, slug):
    provider = get_object_or_404(Provider.objects.publicos().select_related('commune', 'category'), slug=slug)
    if not es_bot(request):
        Provider.objects.filter(pk=provider.pk).update(whatsapp_clicks_count=F('whatsapp_clicks_count') + 1)
        registrar(request, LeadEvent.WHATSAPP_CLICK, origen=request.GET.get('desde', 'provider_detail')[:40],
                  provider=provider, category_slug=provider.category.slug,
                  commune_slug=provider.commune.slug, group=provider.category.group)

    message = 'Hola, vi tu perfil en SERVIPLACE y quiero hacerte una consulta.'
    return redirect(f'https://wa.me/{provider.clean_whatsapp_number}?text={quote(message)}')

