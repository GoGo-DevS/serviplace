"""/llms.txt (20-11-2026): ServiPlace explicado para los asistentes con IA.

Una usuaria llegó porque su asistente con IA le recomendó ServiPlace. El archivo
lista qué es el sitio, los rubros que tienen perfiles y las guías, sin datos de personas.
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from core import guias
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class LlmsTxt(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        Provider.objects.create(
            owner=User.objects.create_user('rodrigo', password='clave-larga-de-verdad-99'),
            business_name='Rodrigo Saavedra', contact_name='Rodrigo Saavedra',
            category=Category.objects.get(slug='gasfiteria'), commune=maipu, sector='Maipú',
            short_description='Gasfitería.', whatsapp_number='56987654321', is_active=True)

    def test_responde_texto_plano_con_lo_que_es_serviplace(self):
        r = self.client.get('/llms.txt')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r['Content-Type'].startswith('text/plain'))
        texto = r.content.decode()
        self.assertTrue(texto.startswith('# ServiPlace\n'))
        self.assertIn('no cobra comisión', texto)
        self.assertIn('/servicios/', texto)

    def test_lista_solo_los_rubros_con_perfiles_publicados(self):
        texto = self.client.get('/llms.txt').content.decode()
        self.assertIn('/servicios/gasfiteria/): 1 perfil', texto)
        self.assertNotIn('/servicios/kinesiologia/', texto)

    def test_incluye_las_guias_y_ningun_dato_de_personas(self):
        texto = self.client.get('/llms.txt').content.decode()
        for g in guias.GUIAS:
            self.assertIn(g['titulo'], texto)
        self.assertNotIn('Rodrigo', texto)
        self.assertNotIn('56987654321', texto)
