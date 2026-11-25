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

    def test_lista_las_paginas_por_especialidad_para_quien_quiere_publicar(self):
        """25-11-2026: ChatGPT manda profesionales a /profesionales/<rubro>/.
        Se listan aunque el rubro no tenga perfiles (es la página para OFRECER)."""
        texto = self.client.get('/llms.txt').content.decode()
        self.assertIn('## Para profesionales: publicar tus servicios gratis', texto)
        self.assertIn('no cobra comisión y los clientes te escriben directo a tu WhatsApp', texto)
        self.assertIn('/profesionales/kinesiologia/)', texto)

    def test_cada_pagina_de_especialidad_listada_existe(self):
        """Al revés: ninguna URL de /profesionales/ del archivo puede dar 404
        (las tiendas y los rubros sin contenido no tienen página)."""
        import re
        texto = self.client.get('/llms.txt').content.decode()
        rutas = re.findall(r'https?://[^/\s)]+(/profesionales/[a-z0-9-]+/)\)', texto)
        self.assertGreater(len(rutas), 10)
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)
        tiendas = Category.objects.filter(group=Category.TIENDAS).values_list('slug', flat=True)
        for slug in tiendas:
            self.assertNotIn(f'/profesionales/{slug}/', texto)

    def test_incluye_las_guias_y_ningun_dato_de_personas(self):
        texto = self.client.get('/llms.txt').content.decode()
        for g in guias.GUIAS:
            self.assertIn(g['titulo'], texto)
        self.assertNotIn('Rodrigo', texto)
        self.assertNotIn('56987654321', texto)
