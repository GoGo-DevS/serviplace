"""Sitio web e Instagram del perfil (18-10-2026)."""
import json
import re
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class WebEInstagram(TestCase):
    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def publicar(self, **extra):
        datos = {
            'business_name': 'Camila Rojas, Kinesióloga', 'contact_name': 'Camila Rojas',
            'category': Category.objects.get(slug='kinesiologia').pk, 'commune': self.maipu.pk, 'sector': 'Centro',
            'short_description': 'Kinesióloga a domicilio en Maipú.', 'description': 'Rehabilitación y adulto mayor.',
            'phone': '+56 9 1111 2222', 'whatsapp_number': '+56 9 1111 2222',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return self.client.post(reverse('accounts:provider_create'), datos)

    def test_instagram_se_guarda_como_usuario_venga_como_venga(self):
        for entrada in ('@camila.kine', 'camila.kine', 'https://www.instagram.com/camila.kine/?hl=es'):
            Provider.objects.all().delete()
            self.assertEqual(self.publicar(instagram=entrada).status_code, 302, entrada)
            self.assertEqual(Provider.objects.get().instagram, 'camila.kine', entrada)

    def test_un_usuario_de_instagram_invalido_se_explica(self):
        respuesta = self.publicar(instagram='camila kine!')
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Escribe solo tu usuario de Instagram')

    def test_la_web_sin_esquema_queda_con_https(self):
        self.publicar(website='tusitio.cl')
        self.assertEqual(Provider.objects.get().website, 'https://tusitio.cl')

    def test_un_enlace_javascript_no_entra(self):
        respuesta = self.publicar(website='javascript:alert(1)')
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Provider.objects.exists())

    def test_la_ficha_los_muestra_como_ugc_y_van_al_schema(self):
        self.publicar(website='https://www.camilakine.cl/', instagram='camila.kine')
        perfil = Provider.objects.get()
        h = self.client.get(perfil.get_absolute_url()).content.decode()
        self.assertIn('href="https://www.camilakine.cl/" target="_blank" rel="ugc noopener"', h)
        self.assertIn('>camilakine.cl</a>', h)
        self.assertIn('href="https://www.instagram.com/camila.kine/" target="_blank" rel="ugc noopener"', h)
        schema = next(json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
                      if '#perfil' in b)
        self.assertEqual(schema['sameAs'], ['https://www.camilakine.cl/', 'https://www.instagram.com/camila.kine/'])
