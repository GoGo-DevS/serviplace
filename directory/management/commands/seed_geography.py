from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Commune, Region


class Command(BaseCommand):
    help = 'Crea regiones/comunas iniciales y asocia Maipú a Región Metropolitana.'

    def handle(self, *args, **options):
        region, _ = Region.objects.update_or_create(
            slug='region-metropolitana',
            defaults={'name': 'Región Metropolitana', 'is_active': True},
        )
        commune, _ = Commune.objects.update_or_create(
            slug=slugify('Maipú'),
            defaults={'name': 'Maipú', 'region': region, 'is_active': True},
        )

        self.stdout.write(self.style.SUCCESS(f'Región lista: {region.name}'))
        self.stdout.write(self.style.SUCCESS(f'Comuna asociada: {commune.name} -> {commune.region.name}'))
