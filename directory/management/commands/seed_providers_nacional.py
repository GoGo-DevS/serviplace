"""
seed_providers_nacional — Prospección de prestadores via Google Maps Places API (New).

Busca "{categoria} {comuna}" en Google Maps y crea Provider prospects en la DB.
A diferencia de GoGoCRM (que quiere negocios SIN web para venderles una), aquí
queremos TODOS: con o sin web. El objetivo es poblar el directorio, no vender webs.

Uso:
    python manage.py seed_providers_nacional
    python manage.py seed_providers_nacional --dry-run
    python manage.py seed_providers_nacional --comunas maipu,las-condes --max-per-query 10
    python manage.py seed_providers_nacional --categorias gasfiteria,cerrajeria

Config (env / settings):
    GOOGLE_MAPS_API_KEY  → key de Google Cloud con Places API (New) habilitada
    GOOGLE_MAPS_REGION   → 'CL' (default)
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Category, Commune, Provider

logger = logging.getLogger(__name__)

# Comunas ordenadas por población estimada (INE 2022).
# Cubrir primero las más grandes maximiza providers reales encontrados.
DEFAULT_COMUNAS_SLUGS = [
    'puente-alto', 'maipu', 'la-florida', 'santiago', 'las-condes',
    'penalolen', 'san-bernardo', 'pudahuel', 'quilicura', 'el-bosque',
    'concepcion', 'vina-del-mar', 'valparaiso', 'temuco', 'antofagasta',
    'la-serena', 'iquique', 'talca', 'arica', 'osorno',
]

_PLACES_URL = 'https://places.googleapis.com/v1/places:searchText'
_FIELDS = (
    'places.displayName,places.websiteUri,places.nationalPhoneNumber,'
    'places.internationalPhoneNumber,places.formattedAddress,places.googleMapsUri,'
    'places.rating,places.userRatingCount,places.primaryTypeDisplayName,nextPageToken'
)
_TIMEOUT = 30


def _buscar_google_maps(query: str, max_items: int = 20) -> list[dict]:
    key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    if not key:
        return [{'error': 'Falta GOOGLE_MAPS_API_KEY en settings/env (Places API New).'}]

    region = getattr(settings, 'GOOGLE_MAPS_REGION', 'CL')
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': key,
        'X-Goog-FieldMask': _FIELDS,
    }

    resultados = []
    page_token = None
    try:
        for _ in range(5):
            body = {'textQuery': query, 'languageCode': 'es', 'regionCode': region}
            if page_token:
                body['pageToken'] = page_token
            req = urllib.request.Request(
                _PLACES_URL,
                data=json.dumps(body).encode('utf-8'),
                headers=headers,
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                out = json.loads(resp.read())
            for place in out.get('places', []):
                nombre = (place.get('displayName') or {}).get('text', '').strip()
                if not nombre:
                    continue
                resultados.append({
                    'nombre':    nombre,
                    'telefono':  (place.get('nationalPhoneNumber') or place.get('internationalPhoneNumber') or '').strip(),
                    'web_url':   (place.get('websiteUri') or '').strip(),
                    'direccion': (place.get('formattedAddress') or '').strip(),
                    'maps_url':  (place.get('googleMapsUri') or '').strip(),
                    'rating':    place.get('rating'),
                    'reviews':   place.get('userRatingCount') or 0,
                    'tipo':      (place.get('primaryTypeDisplayName') or {}).get('text', '').strip(),
                })
            if len(resultados) >= max_items:
                break
            page_token = out.get('nextPageToken')
            if not page_token:
                break
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode('utf-8', 'ignore')[:400]
        try:
            msg = json.loads(detalle).get('error', {}).get('message', detalle)
        except Exception:
            msg = detalle
        return [{'error': f'Google Maps {exc.code}: {msg}'}]
    except Exception as exc:  # noqa: BLE001
        return [{'error': f'Error Google Maps: {str(exc)[:200]}'}]

    return resultados[:max_items]


def _short_desc(nombre: str, categoria_nombre: str, commune_name: str) -> str:
    txt = f'{categoria_nombre} en {commune_name}. Dato público obtenido de Google Maps.'
    return txt[:220]


def _desc(nombre: str, categoria_nombre: str, commune_name: str, direccion: str, rating, reviews: int) -> str:
    partes = [f'Prestador de {categoria_nombre} en {commune_name}.']
    if direccion:
        partes.append(f'Dirección referencial: {direccion}.')
    if rating:
        partes.append(f'Calificación en Google Maps: {rating}/5 ({reviews} reseñas).')
    partes.append('Perfil importado como prospecto público — pendiente de verificación.')
    return ' '.join(partes)


class Command(BaseCommand):
    help = 'Importa prestadores desde Google Maps Places API a las comunas seleccionadas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--comunas',
            default='',
            help='Slugs de comunas separados por coma. Default: top 20 por población.',
        )
        parser.add_argument(
            '--categorias',
            default='',
            help='Slugs de categorías separados por coma. Default: todas las activas.',
        )
        parser.add_argument(
            '--max-per-query',
            type=int,
            default=20,
            help='Máx resultados por búsqueda (default 20).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='No guarda nada — muestra qué importaría.',
        )

    def handle(self, *args, **opts):
        # Forzar UTF-8 en consola Windows
        for stream in (self.stdout, self.stderr):
            try:
                stream._out.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

        dry = opts['dry_run']
        max_q = opts['max_per_query']

        if not getattr(settings, 'GOOGLE_MAPS_API_KEY', ''):
            self.stderr.write(self.style.ERROR('Falta GOOGLE_MAPS_API_KEY. Agrega al .env y reintenta.'))
            return

        # Resolver comunas
        if opts['comunas']:
            slugs = [s.strip() for s in opts['comunas'].split(',') if s.strip()]
        else:
            slugs = DEFAULT_COMUNAS_SLUGS

        comunas = list(Commune.objects.filter(slug__in=slugs, is_active=True).select_related('region'))
        encontrados = {c.slug for c in comunas}
        no_encontrados = [s for s in slugs if s not in encontrados]
        if no_encontrados:
            self.stderr.write(self.style.WARNING(f'Comunas no encontradas en DB: {", ".join(no_encontrados)}'))
        if not comunas:
            self.stderr.write(self.style.ERROR('Sin comunas válidas. Ejecuta seed_regiones_chile primero.'))
            return

        # Resolver categorías
        if opts['categorias']:
            cat_slugs = [s.strip() for s in opts['categorias'].split(',') if s.strip()]
            categorias = list(Category.objects.filter(slug__in=cat_slugs, is_active=True))
        else:
            categorias = list(Category.objects.filter(is_active=True))

        if not categorias:
            self.stderr.write(self.style.ERROR('Sin categorías válidas.'))
            return

        self.stdout.write(
            f'\nBuscando {len(categorias)} categorías × {len(comunas)} comunas '
            f'= {len(categorias) * len(comunas)} queries (max {max_q} resultados c/u).'
        )
        if dry:
            self.stdout.write(self.style.WARNING('  [DRY-RUN — no se guardará nada]'))

        total_creados = 0
        total_skipped = 0
        total_errores = 0

        for comuna in comunas:
            for categoria in categorias:
                query = f'{categoria.name} {comuna.name}'
                self.stdout.write(f'  → {query}', ending=' ')
                self.stdout.flush()

                resultados = _buscar_google_maps(query, max_q)

                if resultados and resultados[0].get('error'):
                    self.stdout.write(self.style.ERROR(f'ERROR: {resultados[0]["error"]}'))
                    total_errores += 1
                    continue

                creados_query = 0
                for r in resultados:
                    nombre = r['nombre']
                    slug_base = slugify(f'{nombre}-{comuna.name}')
                    slug = slug_base
                    counter = 2
                    # Dedup: mismo nombre + misma comuna
                    if Provider.objects.filter(business_name=nombre, commune=comuna).exists():
                        total_skipped += 1
                        continue
                    # Slug único
                    while Provider.objects.filter(slug=slug).exists():
                        slug = f'{slug_base}-{counter}'
                        counter += 1

                    if dry:
                        creados_query += 1
                        total_creados += 1
                        continue

                    Provider.objects.create(
                        business_name=nombre,
                        slug=slug,
                        contact_name='',
                        category=categoria,
                        commune=comuna,
                        sector=r['direccion'][:120] if r['direccion'] else comuna.name,
                        description=_desc(
                            nombre, categoria.name, comuna.name,
                            r['direccion'], r['rating'], r['reviews'],
                        ),
                        short_description=_short_desc(nombre, categoria.name, comuna.name),
                        phone=r['telefono'],
                        whatsapp_number=r['telefono'],
                        email='',
                        address=r['direccion'][:180] if r['direccion'] else '',
                        service_area=f'{comuna.name} y alrededores',
                        is_verified=False,
                        is_featured=False,
                        is_active=True,
                        source_name='Google Maps',
                        source_url=r['maps_url'],
                        source_notes=(
                            f'Query: {query} | Rating: {r["rating"]} ({r["reviews"]} reseñas) '
                            f'| Web: {r["web_url"] or "sin web"} | Tipo: {r["tipo"]}'
                        ),
                        data_status=Provider.PUBLIC_PROSPECT,
                    )
                    creados_query += 1
                    total_creados += 1

                self.stdout.write(self.style.SUCCESS(f'{creados_query} nuevos'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Listo{"  [DRY-RUN]" if dry else ""}. '
            f'Creados: {total_creados} | Duplicados saltados: {total_skipped} | Errores API: {total_errores}'
        ))
