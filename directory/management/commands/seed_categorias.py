"""
Crea las 9 categorías base si no existen. Idempotente y NO pisa: si la categoría
ya existe no le cambia nombre, descripción ni icono (eso se edita en el admin).
Va en build.sh porque una base Postgres nueva arranca sin categorías y sin ellas
no se puede publicar nada.
"""
from django.core.management.base import BaseCommand

from directory.models import Category

CATEGORIAS = [
    ('gasfiteria', 'Gasfitería', 'Filtraciones, calefont, WC, grifería y destapes.'),
    ('electricidad', 'Electricidad', 'Instalaciones, tableros, enchufes y reparaciones eléctricas.'),
    ('cerrajeria', 'Cerrajería', 'Apertura de puertas, cambio de chapas y copias de llaves.'),
    ('climatizacion', 'Climatización', 'Instalación y mantención de aire acondicionado y calefacción.'),
    ('construccion', 'Construcción', 'Obras menores, ampliaciones, remodelaciones y terminaciones.'),
    ('limpieza', 'Limpieza', 'Aseo domiciliario, de oficinas y post obra.'),
    ('jardineria', 'Jardinería', 'Poda, riego, pasto y mantención de jardines.'),
    ('carpinteria', 'Carpintería', 'Muebles, puertas, closets y trabajos en madera.'),
    ('pintura', 'Pintura', 'Pintura interior, exterior y reparación de muros.'),
]


class Command(BaseCommand):
    help = 'Crea las categorías base si faltan (idempotente, no sobreescribe).'

    def handle(self, *args, **options):
        creadas = 0
        for orden, (slug, nombre, desc) in enumerate(CATEGORIAS, start=1):
            _, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': nombre, 'description': desc, 'icon': slug, 'display_order': orden, 'is_active': True},
            )
            creadas += int(created)
        self.stdout.write(f'Categorías: {creadas} creadas, {Category.objects.count()} en total.')
