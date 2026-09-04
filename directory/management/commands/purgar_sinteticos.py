"""
Saca del directorio los prestadores INVENTADOS. Un directorio público con
gásfiters que no existen engaña al que busca uno.

  - source_name='seed_offline'  → 177 sintéticos del seed offline (27-06-2026). SE BORRAN.
  - demo de seed_initial_data   → 10 de Maipú con teléfono +56 9 1111 00XX. NO se borran
                                  (regla: los 32 de Maipú no se tocan): se OCULTAN con
                                  --ocultar-demo, reversible con --mostrar-demo.

Dry-run por defecto. Escribe solo con --confirmar. Idempotente.
Respaldo previo obligatorio: dumpdata a un JSON FUERA del repo (ver DEPLOY.md).
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from directory.models import Provider

DEMO_PHONE_PREFIX = '+56 9 1111 00'


def sinteticos_qs():
    return Provider.objects.filter(source_name='seed_offline')


def demo_maipu_qs():
    return Provider.objects.filter(
        source_name='',
        phone__startswith=DEMO_PHONE_PREFIX,
        owner__isnull=True,
    )


class Command(BaseCommand):
    help = 'Borra prestadores sintéticos (seed_offline) y oculta los demo de Maipú. Dry-run por defecto.'

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true', help='Escribe de verdad. Sin esto solo informa.')
        parser.add_argument('--ocultar-demo', action='store_true', help='Además oculta (is_active=False) los 10 demo de Maipú.')
        parser.add_argument('--mostrar-demo', action='store_true', help='Reversa: vuelve a mostrar los demo de Maipú.')

    def handle(self, *args, **opts):
        for stream in (self.stdout, self.stderr):
            try:
                stream._out.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

        confirmar = opts['confirmar']
        sint = sinteticos_qs()
        demo = demo_maipu_qs()
        n_sint = sint.count()
        n_demo = demo.count()
        n_demo_activos = demo.filter(is_active=True).count()

        self.stdout.write(f'Sintéticos (seed_offline) a borrar : {n_sint}')
        self.stdout.write(f'Demo de Maipú (tel 1111 00XX)      : {n_demo} ({n_demo_activos} visibles)')
        reales = Provider.objects.exclude(source_name='seed_offline').exclude(pk__in=demo.values('pk')).count()
        self.stdout.write(f'Reales que NO se tocan             : {reales}')

        if not confirmar:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] No se escribió nada. Agrega --confirmar para ejecutar.'))
            return

        with transaction.atomic():
            borrados = 0
            if n_sint:
                borrados, _ = sint.delete()
            ocultos = 0
            mostrados = 0
            if opts['ocultar_demo']:
                ocultos = demo.filter(is_active=True).update(
                    is_active=False,
                    hidden_at=timezone.now(),
                    moderation_note='Demo de seed_initial_data (teléfono inventado). Oculto el 04-09-2026 antes de publicar.',
                )
            if opts['mostrar_demo']:
                mostrados = demo.filter(is_active=False).update(is_active=True, hidden_at=None)

        self.stdout.write(self.style.SUCCESS(
            f'\nListo. Borrados: {borrados} | Demo ocultos: {ocultos} | Demo mostrados: {mostrados} | '
            f'Quedan activos: {Provider.objects.filter(is_active=True).count()}'
        ))
