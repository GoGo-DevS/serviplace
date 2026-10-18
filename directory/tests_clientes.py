"""Perfiles de los clientes de GoGoDevS (18-10-2026): cargar_clientes."""
import re
import shutil
import tempfile
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.forms import normalizar_movil
from directory.clientes_gogodevs import CLIENTES, FUENTE
from directory.models import Category, Commune, Provider

User = get_user_model()


class CargarClientes(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_regiones_chile', stdout=StringIO())
        call_command('seed_categorias', stdout=StringIO())

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        self.diego = User.objects.create_superuser('diego', 'd@example.cl', 'clave-larga-de-verdad-99')

    def cargar(self, dueno='diego'):
        salida = StringIO()
        with override_settings(MEDIA_ROOT=self.media):
            call_command('cargar_clientes', dueno=dueno, stdout=salida)
        return salida.getvalue()

    def test_crea_todos_publicos_con_logo_web_e_instagram(self):
        self.cargar()
        perfiles = Provider.objects.filter(source_name=FUENTE)
        self.assertEqual(perfiles.count(), len(CLIENTES))
        self.assertEqual(Provider.objects.publicos().filter(source_name=FUENTE).count(), len(CLIENTES),
                         'sin dueño un perfil no es público')
        for p in perfiles:
            self.assertTrue(p.foto, f'{p.business_name} sin logo')
            self.assertTrue(p.website.startswith('https://'), p.business_name)
            self.assertEqual(p.owner, self.diego)
            self.assertEqual(p.data_status, Provider.AUTHORIZED)

    def test_correr_dos_veces_no_duplica_ni_pisa(self):
        self.cargar()
        Provider.objects.filter(source_name=FUENTE, business_name='Púas Tatuajes').update(
            short_description='Editado por Diego en el panel.')
        salida = self.cargar()
        self.assertEqual(Provider.objects.filter(source_name=FUENTE).count(), len(CLIENTES))
        self.assertEqual(Provider.objects.get(business_name='Púas Tatuajes').short_description,
                         'Editado por Diego en el panel.')
        self.assertIn('0 creados', salida)

    def test_si_el_cliente_ya_se_inscribio_solo_no_se_duplica(self):
        """Dulcecita se estaba inscribiendo sola el 18-10: con su mismo WhatsApp,
        la carga no le crea un segundo perfil."""
        dueña = User.objects.create_user('dulcecita', password='clave-larga-de-verdad-99')
        Provider.objects.create(
            business_name='Dulcecita Repostería', contact_name='Dulcecita', owner=dueña,
            category=Category.objects.get(slug='reposteria-y-dulces'), commune=Commune.objects.get(slug='santiago'),
            sector='Centro', description='Lo que ella escribió.', short_description='Su descripción.',
            phone='+56 9 6119 2192', whatsapp_number='56961192192', is_active=True)
        self.cargar()
        self.assertEqual(Provider.objects.filter(whatsapp_number='56961192192').count(), 1)
        self.assertEqual(Provider.objects.get(whatsapp_number='56961192192').owner, dueña)

    def test_un_cliente_desactivado_no_vuelve(self):
        self.cargar()
        Provider.objects.filter(business_name='Medina4x4').update(is_active=False)
        self.cargar()
        self.assertFalse(Provider.objects.get(business_name='Medina4x4').is_active)

    def test_sin_el_dueno_no_carga_nada_ni_rompe_el_deploy(self):
        salida = self.cargar(dueno='no-existe')
        self.assertIn('no se carga ningún cliente', salida)
        self.assertFalse(Provider.objects.filter(source_name=FUENTE).exists())

    def test_los_datos_son_coherentes_con_el_formulario(self):
        """Lo que entra por la carga cumple las mismas reglas que lo que entra
        por el formulario: celular chileno, teléfono con formato, rubro y comuna
        que existen."""
        for c in CLIENTES:
            self.assertEqual(normalizar_movil(c['whatsapp']), c['whatsapp'], c['slug'])
            self.assertRegex(c['telefono'], r'^\+56 [2-9] \d{4} \d{4}$', c['slug'])
            self.assertTrue(Category.objects.filter(slug=c['rubro'], is_active=True).exists(), c['slug'])
            self.assertTrue(Commune.objects.filter(slug=c['comuna']).exists(), c['slug'])
            self.assertLessEqual(len(c['corta']), 220, c['slug'])
            self.assertNotIn('$', c['larga'], f"{c['slug']}: sin precios (G-01)")
            if c.get('instagram'):
                self.assertRegex(c['instagram'], r'^[A-Za-z0-9._]{1,30}$', c['slug'])

    def test_la_ficha_y_el_listado_de_una_tienda(self):
        self.cargar()
        medina = Provider.objects.get(business_name='Medina4x4')
        h = self.client.get(medina.get_absolute_url()).content.decode()
        self.assertIn('href="https://medina4x4.cl"', h)
        self.assertIn('@repuestosmedina4x4', h)
        self.assertIn('"@type":"AutoPartsStore"', h)
        listado = self.client.get('/servicios/repuestos-automotrices/santiago/').content.decode()
        self.assertIn('Medina4x4', listado)
        self.assertIn('Comercial Villarreal', listado)
        self.assertNotIn('su formación', listado, 'una tienda no tiene formación')
        # No lo publicó el dueño en persona: la tarjeta no puede decir que sí
        self.assertIn('Datos de su sitio web oficial', listado)
        self.assertNotIn('Publicado por su dueño', listado)

    def test_las_tiendas_no_tienen_pagina_para_profesionales(self):
        self.assertEqual(self.client.get('/profesionales/repuestos-automotrices/').status_code, 404)
        self.assertEqual(self.client.get('/profesionales/tatuajes/').status_code, 200)
        self.assertNotIn('/profesionales/automotoras/</loc>', self.client.get('/sitemap.xml').content.decode())
