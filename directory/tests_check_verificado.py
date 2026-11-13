"""Insignia azul de Verificado (13-11-2026).

Diego: "que sea como un ticket azul de Meta, TikTok, Twitter". Lo que se
protege: que la insignia salga junto al nombre (ficha, listado y la historia de
Instagram) SOLO cuando la regla de siempre se cumple (is_verified y con dueño),
y que no salga en un perfil sin verificar ni en uno importado sin dueño aunque
el campo diga True (el caso de los 12 de Maipú del 18-10).
"""
import io
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from directory import historia
from directory.models import Category, Commune, Provider, Region

User = get_user_model()
MARCA = 'data-check-verificado'


def pixeles_azules(jpeg):
    """Píxeles del azul de la insignia (#1d8cf8) en la historia; el JPEG los mueve un poco."""
    imagen = Image.open(io.BytesIO(jpeg)).convert('RGB')
    return sum(n for n, (r, g, b) in imagen.getcolors(maxcolors=1 << 24)
               if abs(r - 29) <= 30 and abs(g - 140) <= 30 and abs(b - 248) <= 30)


class InsigniaAzulDeVerificado(TestCase):

    def setUp(self):
        cache.clear()
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = Category.objects.get(slug='gasfiteria')
        self.dueno = User.objects.create_user('camila', password='clave-larga-de-verdad-99')

    def _perfil(self, nombre, verificado, dueno=True):
        return Provider.objects.create(
            owner=self.dueno if dueno else None, business_name=nombre, category=self.cat, commune=self.maipu,
            sector='Ciudad Satélite', short_description='Calefont, filtraciones y destapes.',
            whatsapp_number='56987654321', is_active=True, is_verified=verificado,
            whatsapp_confirmado_en=timezone.now() if verificado else None)

    def _ficha(self, p):
        return self.client.get(p.get_absolute_url()).content.decode()

    def test_el_verificado_lleva_la_insignia_junto_al_nombre_en_su_ficha(self):
        p = self._perfil('Gasfitería Camila', verificado=True)
        html = self._ficha(p)
        self.assertIn(MARCA, html)
        h1 = html[html.index('<h1'):html.index('</h1>')]
        self.assertIn('Gasfitería Camila', h1)
        self.assertIn(MARCA, h1)
        self.assertIn('Verificado por ServiPlace', html)

    def test_sin_verificar_no_hay_insignia(self):
        self.assertNotIn(MARCA, self._ficha(self._perfil('Gasfitería Pedro', verificado=False)))

    def test_importado_sin_dueno_no_lleva_insignia_aunque_el_campo_diga_verificado(self):
        p = self._perfil('Gasfitería Importada', verificado=True, dueno=False)
        self.assertTrue(p.is_verified)
        self.assertNotIn(MARCA, self._ficha(p))

    def test_en_el_listado_la_insignia_va_solo_en_la_tarjeta_del_verificado(self):
        self._perfil('Gasfitería Camila', verificado=True)
        self._perfil('Gasfitería Pedro', verificado=False)
        html = self.client.get(reverse('directory:listado_rubro', args=['gasfiteria'])).content.decode()
        self.assertEqual(html.count(MARCA), 1)
        # La tarjeta, no el JSON-LD del encabezado: el h3 con el enlace a la ficha.
        i = html.index('>Gasfitería Camila</a>')
        self.assertIn(MARCA, html[i:i + 1500].split('</h3>')[0])
        j = html.index('>Gasfitería Pedro</a>')
        self.assertNotIn(MARCA, html[j:j + 1500].split('</h3>')[0])

    def test_la_historia_del_verificado_lleva_el_azul_de_la_insignia(self):
        con = historia.dibujar(self._perfil('Gasfitería Camila', verificado=True))
        sin = historia.dibujar(self._perfil('Gasfitería Pedro', verificado=False))
        self.assertGreater(pixeles_azules(con), 600)
        self.assertLess(pixeles_azules(sin), 50)
