"""Crea los perfiles de los clientes de GoGoDevS que falten (18-10-2026).

Pedido de Diego: "métele datos a ServiPlace, los de mis clientes, con todo lo
de ellos: logo, nombre, todo". Son negocios reales que GoGoDevS conoce, con
sus datos tomados de su propio sitio público (ver directory/clientes_gogodevs.py,
cada uno con su fuente).

Reglas:
- Corre en cada deploy (build.sh) y es idempotente: un cliente que ya tiene
  perfil NO se toca, aunque se haya editado o desactivado en el admin (memoria
  seed_data_no_sobreescribir). La llave es la web del cliente.
- Si el cliente ya se inscribió SOLO (mismo WhatsApp o misma web), tampoco se
  crea: Dulcecita se estaba inscribiendo el 18-10 y la carga le habría
  duplicado el perfil.
- Para sacar a un cliente: desactivarlo en el admin. Si se BORRA, vuelve en el
  próximo deploy; para que no vuelva, sacarlo también de la lista.
- Dueño: el usuario admin de Diego (DJANGO_SUPERUSER_USERNAME), así los edita
  desde su panel. Sin ese usuario no se carga nada (no rompe el deploy).
- Los logos vienen en directory/clientes_logos/ ya procesados (WebP <100 KB) y
  se suben al almacenamiento configurado (R2 en producción).
"""
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from directory.clientes_gogodevs import CLIENTES, FUENTE
from directory.models import Category, Commune, Provider, ProviderImage

LOGOS = Path(__file__).resolve().parents[2] / 'clientes_logos'
FOTOS = Path(__file__).resolve().parents[2] / 'clientes_fotos'


class Command(BaseCommand):
    help = 'Crea los perfiles de los clientes de GoGoDevS que falten (idempotente, nunca pisa).'

    def add_arguments(self, parser):
        parser.add_argument('--dueno', default=os.environ.get('DJANGO_SUPERUSER_USERNAME', ''),
                            help='Usuario dueño de los perfiles (por defecto, el admin del deploy).')

    def handle(self, *args, dueno, **options):
        usuario = get_user_model().objects.filter(username=dueno).first() if dueno else None
        if not usuario:
            self.stdout.write(self.style.WARNING(
                f'cargar_clientes: no existe el usuario "{dueno}"; no se carga ningún cliente.'))
            return
        creados, ya_estaban = [], 0
        for cliente in CLIENTES:
            web = cliente['web'].rstrip('/')
            ya_existe = Provider.objects.filter(
                Q(source_name=FUENTE, source_url=cliente['web'])
                | Q(whatsapp_number=cliente['whatsapp'])
                | Q(website__in=[web, web + '/'])
            ).exists()
            if ya_existe:
                ya_estaban += 1
                continue
            categoria = Category.objects.filter(slug=cliente['rubro'], is_active=True).first()
            comuna = Commune.objects.filter(slug=cliente['comuna']).first()
            if not categoria or not comuna:
                self.stdout.write(self.style.WARNING(
                    f"cargar_clientes: {cliente['nombre']} sin rubro o comuna válidos; se omite."))
                continue
            perfil = Provider(
                business_name=cliente['nombre'],
                contact_name=cliente.get('contacto') or cliente['nombre'],
                owner=usuario,
                category=categoria,
                commune=comuna,
                sector=cliente['sector'],
                short_description=cliente['corta'],
                description=cliente['larga'],
                phone=cliente['telefono'],
                whatsapp_number=cliente['whatsapp'],
                email=cliente.get('email', ''),
                address=cliente.get('direccion', ''),
                service_area=cliente.get('atiende', ''),
                website=cliente['web'],
                instagram=cliente.get('instagram', ''),
                attends_home=cliente.get('a_domicilio', False),
                attends_office=cliente.get('en_local', False),
                attends_online=cliente.get('online', False),
                is_active=True,
                data_status=Provider.AUTHORIZED,
                claimed_at=timezone.now(),
                source_name=FUENTE,
                source_url=cliente['web'],
                source_notes=f"Cliente de GoGoDevS. Datos de su sitio público: {', '.join(cliente['fuentes'])}",
            )
            logo = LOGOS / f"{cliente['slug']}.webp"
            if logo.exists():
                perfil.foto.save(logo.name, ContentFile(logo.read_bytes()), save=False)
            perfil.save()
            creados.append(perfil.business_name)
        con_fotos = self._fotos()
        self.stdout.write(f'cargar_clientes: {len(creados)} creados, {ya_estaban} ya estaban, '
                          f'{con_fotos} con fotos nuevas.' + (f" ({', '.join(creados)})" if creados else ''))

    def _fotos(self):
        """Fotos de su sitio para los perfiles que cargó esta carga y que todavía
        no tienen ninguna. Si el dueño ya subió las suyas, no se tocan; a un
        cliente que se inscribió solo, tampoco (su perfil no es de la carga)."""
        n = 0
        for cliente in CLIENTES:
            perfil = Provider.objects.filter(source_name=FUENTE, source_url=cliente['web']).first()
            if not perfil or not cliente.get('fotos') or perfil.images.exists():
                continue
            for orden, (archivo, alt) in enumerate(cliente['fotos']):
                ruta = FOTOS / cliente['slug'] / archivo
                if not ruta.exists():
                    continue
                imagen = ProviderImage(provider=perfil, alt_text=alt[:160], is_cover=(orden == 0), display_order=orden)
                imagen.image.save(f"{cliente['slug']}-{orden + 1}.webp", ContentFile(ruta.read_bytes()), save=False)
                imagen.save()
            n += 1
        return n
