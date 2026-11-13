"""Sellos con ícono, sector sin doble puntuación y un solo botón de WhatsApp en
el teléfono (13-11-2026, capturas de Diego de su propia ficha).

- Los tres sellos salen con su ícono desde una sola plantilla, en la ficha y en
  el listado, y solo si están comprobados.
- "Santiago." + Maipú se leía "Santiago., Maipú": el sector se muestra sin la
  puntuación final, y no se repite si es igual a la comuna.
- En el teléfono salían dos botones de WhatsApp seguidos: la regla que esconde
  el de la tarjeta perdía contra .d-flex de Bootstrap.
"""
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class SellosConIcono(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.kine = Category.objects.get(slug='kinesiologia')
        self.dueno = User.objects.create_user('camila', password='clave-larga-de-verdad-99')

    def _perfil(self, nombre='Kine Camila', sector='Ciudad Satélite', **extra):
        return Provider.objects.create(
            owner=self.dueno, business_name=nombre, category=self.kine, commune=self.maipu,
            sector=sector, short_description='Kinesiología a domicilio.', whatsapp_number='56987654321',
            is_active=True, **extra)

    def test_los_tres_sellos_salen_con_su_icono_en_la_ficha_y_en_el_listado(self):
        ahora = timezone.now()
        p = self._perfil(whatsapp_confirmado_en=ahora, registro_salud_comprobado_en=ahora,
                         health_registry='123456', licencia_sec_comprobada_en=ahora, licencia_sec='SEC-1')
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        listado = self.client.get(reverse('directory:listado_rubro', args=['kinesiologia'])).content.decode()
        for html in (ficha, listado):
            for sello, texto in (('whatsapp', 'WhatsApp confirmado'), ('salud', 'Registro de salud comprobado'),
                                 ('sec', 'Licencia SEC comprobada')):
                i = html.index(f'data-sello="{sello}"')
                # WhatsApp es solo el logo con el visto ("Opción A"); el texto queda oculto
                # para lectores de pantalla. Salud y SEC siguen con ícono y texto.
                self.assertIn('class="wa-logo"' if sello == 'whatsapp' else 'class="sello-ico"', html[i:i + 300])
                self.assertIn(texto, html[i:i + 2400])

    def test_sin_comprobar_no_hay_sellos(self):
        html = self.client.get(self._perfil().get_absolute_url()).content.decode()
        self.assertNotIn('data-sello=', html)

    def test_el_sector_se_muestra_sin_la_puntuacion_final(self):
        p = self._perfil(sector='Santiago.')
        self.assertEqual(p.sector_limpio, 'Santiago')
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertNotIn('Santiago.,', html)
        self.assertNotIn('Santiago. ·', html)
        self.assertIn('Santiago, Maipú', html)

    def test_si_el_sector_repite_la_comuna_no_se_dice_dos_veces(self):
        p = self._perfil(sector='Maipú')
        self.assertEqual(p.sector_limpio, '')
        self.assertNotIn('Maipú, Maipú', self.client.get(p.get_absolute_url()).content.decode())


class UnSoloBotonDeWhatsappEnElTelefono(TestCase):

    def test_la_regla_que_esconde_el_boton_de_la_tarjeta_le_gana_a_d_flex(self):
        css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'site.css').read_text(encoding='utf-8')
        movil = css[css.index('@media (max-width: 767px)'):]
        self.assertIn('.desktop-whatsapp-button { display: none !important; }', movil)
