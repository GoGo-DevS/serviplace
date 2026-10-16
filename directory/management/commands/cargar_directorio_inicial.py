"""Carga el directorio inicial (361 prestadores reales) en una base VACÍA.

Corre en cada build de Render, pero solo actúa la primera vez: si la base ya
tiene regiones o prestadores no toca nada. Así un deploy nunca pisa lo que
los usuarios publicaron o editaron en producción.

El fixture sale del respaldo local del 16-10-2026 y trae solo lo publicado:
regiones, comunas, categorías y los prestadores ACTIVOS (todos con fuente y
URL de origen). Los ocultos por curación y los 10 de prueba con teléfono
inventado se quedaron fuera a propósito. Los contadores de visitas y clics
van en cero: los locales eran ruido de pruebas, no tráfico real.

Va ANTES de `seed_regiones_chile` porque el fixture trae las claves
primarias originales: las comunas tienen que ser las mismas a las que
apuntan los prestadores.
"""
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from directory.models import Provider, Region

FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'directorio_inicial.json'


class Command(BaseCommand):
    help = 'Carga el directorio inicial solo si la base está vacía.'

    def handle(self, *args, **options):
        if Provider.objects.exists() or Region.objects.exists():
            self.stdout.write(
                f'Directorio ya cargado ({Provider.objects.count()} prestadores, '
                f'{Region.objects.count()} regiones): no se toca nada.'
            )
            return

        call_command('loaddata', str(FIXTURE), verbosity=0)
        self.stdout.write(self.style.SUCCESS(
            f'Directorio inicial cargado: {Provider.objects.count()} prestadores '
            f'({Provider.objects.filter(is_active=True).count()} activos), '
            f'{Region.objects.count()} regiones.'
        ))
