"""Panel interno de métricas del embudo (`/cuenta/metricas/`, solo staff).

Responde una sola pregunta, cada semana: ¿en qué parte del directorio se
pierde la oportunidad? Faltan perfiles (búsquedas sin resultados), las fichas
no convencen (vistas sin clic), o el profesional se cae antes de publicar.

Todo con consultas agregadas (G-04): el panel no puede hacer una consulta por
comuna ni por día.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from directory.models import Category, Commune, Provider
from leads.models import LeadEvent

PERIODOS = (7, 30, 90)


def _tasa(parte, total):
    return round(100 * parte / total, 1) if total else None


def diagnostico(visitantes, busquedas, sin_resultados, vistas, clics, registros_iniciados, cuentas):
    """La lectura del embudo en una frase, con las reglas del plan de 21 días.

    Es orientativa: con poco tráfico ninguna tasa significa nada, y eso es lo
    primero que dice.
    """
    if visitantes < 30:
        return ('E', 'Muy poco tráfico para sacar conclusiones (menos de 30 visitantes en el período). '
                     'Prioridad: difusión directa y captación manual de perfiles, no cambios de diseño.')
    if busquedas >= 10 and sin_resultados / busquedas >= 0.3:
        return ('A', 'Muchas búsquedas terminan sin resultados. Prioridad: captar perfiles en las '
                     'especialidades y comunas de la tabla "Búsquedas sin resultados".')
    if busquedas >= 10 and vistas / busquedas < 0.3:
        return ('B', 'Hay resultados, pero pocos abren una ficha. Revisar las tarjetas del listado y el orden.')
    if vistas >= 20 and clics / vistas < 0.05:
        return ('C', 'Abren fichas, pero casi nadie escribe por WhatsApp. Revisar la información de las fichas y la confianza.')
    if registros_iniciados >= 10 and cuentas / registros_iniciados < 0.3:
        return ('D', 'Muchos empiezan el registro y pocos lo terminan. Revisar el formulario y la explicación de beneficios.')
    return ('—', 'Sin una alerta clara en este período. Seguir midiendo y comparar con el período anterior.')


@login_required
def metricas(request):
    if not request.user.is_staff:
        raise Http404  # no se anuncia que existe
    try:
        dias = int(request.GET.get('dias', 30))
    except ValueError:
        dias = 30
    if dias not in PERIODOS:
        dias = 30
    desde = timezone.now() - timedelta(days=dias)
    eventos = LeadEvent.objects.filter(created_at__gte=desde)

    conteo = dict(eventos.values_list('event_type').annotate(n=Count('id')))
    busquedas = conteo.get(LeadEvent.SEARCH, 0)
    sin_resultados = eventos.filter(event_type=LeadEvent.SEARCH, results_count=0).count()
    vistas = conteo.get(LeadEvent.DETAIL_VIEW, 0)
    clics = conteo.get(LeadEvent.WHATSAPP_CLICK, 0)
    visitas_portada = eventos.filter(event_type=LeadEvent.PAGE_VIEW, source_page='home').count()
    visitas_landing = eventos.filter(event_type=LeadEvent.PAGE_VIEW, source_page='profesionales').count()
    registros_iniciados = conteo.get(LeadEvent.SIGNUP_STARTED, 0)
    cuentas = conteo.get(LeadEvent.SIGNUP_DONE, 0)
    publicados = conteo.get(LeadEvent.PROFILE_PUBLISHED, 0)
    visitantes = eventos.exclude(visitor='').values('visitor').distinct().count()

    nombres_cat = dict(Category.objects.values_list('slug', 'name'))
    nombres_com = dict(Commune.objects.values_list('slug', 'name'))

    def _etiquetar(filas):
        for fila in filas:
            fila['categoria'] = nombres_cat.get(fila.get('category_slug'), '') or ''
            fila['comuna'] = nombres_com.get(fila.get('commune_slug'), '') or ''
        return filas

    sin_resultado_top = _etiquetar(list(
        eventos.filter(event_type=LeadEvent.SEARCH, results_count=0)
        .values('category_slug', 'commune_slug', 'query').annotate(n=Count('id')).order_by('-n')[:12]
    ))
    buscado_top = _etiquetar(list(
        eventos.filter(event_type=LeadEvent.SEARCH).exclude(category_slug='')
        .values('category_slug').annotate(n=Count('id')).order_by('-n')[:8]
    ))
    perfiles_top = list(
        eventos.filter(event_type__in=[LeadEvent.DETAIL_VIEW, LeadEvent.WHATSAPP_CLICK], provider__isnull=False)
        .values('provider__business_name', 'provider__slug', 'provider__commune__name')
        .annotate(vistas=Count('id', filter=Q(event_type=LeadEvent.DETAIL_VIEW)),
                  clics=Count('id', filter=Q(event_type=LeadEvent.WHATSAPP_CLICK)))
        .order_by('-clics', '-vistas')[:10]
    )

    serie = {}
    for fila in (eventos.annotate(dia=TruncDate('created_at')).values('dia', 'event_type')
                 .annotate(n=Count('id')).order_by('-dia')):
        serie.setdefault(fila['dia'], {})[fila['event_type']] = fila['n']
    serie_dias = [{'dia': dia, **valores} for dia, valores in sorted(serie.items(), reverse=True)][:31]

    activos = Provider.objects.filter(is_active=True)
    oferta = activos.aggregate(
        total=Count('id'),
        autoservicio=Count('id', filter=Q(owner__isnull=False)),
        importados=Count('id', filter=Q(owner__isnull=True)),
    )
    por_grupo = dict(activos.values_list('category__group').annotate(n=Count('id')))
    grupos = [{'nombre': nombre, 'n': por_grupo.get(clave, 0)} for clave, nombre, _ in Category.GRUPOS]
    # Incompleto = lo publicó su dueño pero le falta lo que más convence:
    # cómo atiende, una descripción que diga algo, o su formación si no es oficio.
    incompletos = activos.filter(owner__isnull=False).filter(
        Q(attends_home=False, attends_office=False, attends_online=False)
        | Q(description__regex=r'^.{0,59}$')
        | (~Q(category__group=Category.HOGAR) & Q(profession_title=''))
    ).count()
    mercado = list(
        activos.values('commune__name', 'category__name').annotate(n=Count('id')).order_by('-n')[:12]
    )
    usuarios_nuevos = get_user_model().objects.filter(date_joined__gte=desde).count()

    contexto = {
        'dias': dias, 'periodos': PERIODOS,
        'busquedas': busquedas, 'sin_resultados': sin_resultados,
        'tasa_sin_resultados': _tasa(sin_resultados, busquedas),
        'vistas': vistas, 'clics': clics, 'tasa_clic': _tasa(clics, vistas),
        'visitas_portada': visitas_portada, 'visitas_landing': visitas_landing,
        'visitantes': visitantes,
        'registros_iniciados': registros_iniciados, 'cuentas': cuentas, 'publicados': publicados,
        'tasa_registro': _tasa(cuentas, registros_iniciados), 'tasa_publicacion': _tasa(publicados, cuentas),
        'usuarios_nuevos': usuarios_nuevos,
        'sin_resultado_top': sin_resultado_top, 'buscado_top': buscado_top, 'perfiles_top': perfiles_top,
        'serie_dias': serie_dias, 'oferta': oferta, 'grupos': grupos, 'incompletos': incompletos,
        'mercado': mercado,
        'diagnostico': diagnostico(visitantes, busquedas, sin_resultados, vistas, clics, registros_iniciados, cuentas),
        'page_title': 'Métricas | ServiPlace', 'robots': 'noindex',
    }
    return render(request, 'core/metricas.html', contexto)
