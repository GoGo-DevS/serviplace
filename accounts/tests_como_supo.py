"""¿Cómo supiste de ServiPlace? (25-11-2026).

Un profesional nuevo le dijo a Diego que lo trajo ChatGPT. GA4 lo ve solo a
medias: la app de ChatGPT a veces no manda referrer y la visita cae en
"directo". Se le pregunta a quien publica su perfil (paso 2, no el registro,
que quedó en correo + contraseña el 15-11), una vez por cuenta y sin obligar.
"""
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class ComoSupoAlPublicar(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.comuna = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.user = User.objects.create_user('ana', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def _publicar(self, nombre='Ana Rojas Contabilidad', **extra):
        datos = {
            'business_name': nombre, 'contact_name': 'Ana Rojas',
            'category': Category.objects.get(slug='contabilidad').pk, 'commune': self.comuna.pk,
            'sector': 'Centro', 'short_description': 'Contabilidad para pymes y emprendedores.',
            'description': 'Llevo la contabilidad de pymes, declaraciones mensuales y renta.',
            'phone': '+56 9 1111 2222', 'whatsapp_number': '+56 9 1111 2222',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return self.client.post(reverse('accounts:provider_create'), datos)

    def test_la_pregunta_aparece_al_publicar_con_chatgpt_como_opcion(self):
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('¿Cómo supiste de ServiPlace? (opcional)', html)
        self.assertIn('<option value="ia">ChatGPT u otra inteligencia artificial</option>', html)
        self.assertIn('name="como_supo"', html)

    def test_la_respuesta_queda_en_la_cuenta(self):
        r = self._publicar(como_supo='ia')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Provider.objects.count(), 1)
        self.assertEqual(UserProfile.objects.get(user=self.user).como_supo, 'ia')

    def test_no_responder_no_impide_publicar(self):
        r = self._publicar()
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Provider.objects.count(), 1)
        self.assertEqual(UserProfile.objects.get(user=self.user).como_supo, '')

    def test_una_respuesta_inventada_no_se_guarda(self):
        r = self._publicar(como_supo='hackeo')
        self.assertEqual(r.status_code, 200)  # el formulario vuelve con el error
        self.assertEqual(Provider.objects.count(), 0)
        self.assertFalse(UserProfile.objects.filter(user=self.user).exclude(como_supo='').exists())

    def test_se_pregunta_una_sola_vez_por_cuenta(self):
        self._publicar(como_supo='google')
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertNotIn('name="como_supo"', html)
        # Un segundo perfil con un valor colado en el POST no pisa la primera respuesta.
        self._publicar(nombre='Ana Rojas Asesorías', como_supo='tiktok')
        self.assertEqual(UserProfile.objects.get(user=self.user).como_supo, 'google')

    def test_al_editar_no_se_pregunta(self):
        self._publicar()
        provider = Provider.objects.get()
        html = self.client.get(reverse('accounts:provider_edit', kwargs={'slug': provider.slug})).content.decode()
        self.assertNotIn('name="como_supo"', html)


class ComoSupoEnLasMetricas(TestCase):

    def test_el_panel_cuenta_las_respuestas_de_las_cuentas_nuevas(self):
        staff = User.objects.create_user('diego', password='clave-larga-de-verdad-99', is_staff=True)
        for i, respuesta in enumerate(['ia', 'ia', 'google', '']):
            u = User.objects.create_user(f'p{i}', password='clave-larga-de-verdad-99')
            UserProfile.objects.update_or_create(user=u, defaults={'como_supo': respuesta})
        self.client.force_login(staff)
        html = self.client.get(reverse('core:metricas')).content.decode()
        self.assertIn('Cómo supieron de ServiPlace', html)
        self.assertRegex(html, r'<td>ChatGPT u otra inteligencia artificial</td><td class="num">2</td>')
        self.assertRegex(html, r'<td>Buscando en Google</td><td class="num">1</td>')
        self.assertIn('<td>Sin respuesta</td>', html)

    def test_el_panel_sigue_cerrado_para_quien_no_es_staff(self):
        u = User.objects.create_user('ana', password='clave-larga-de-verdad-99')
        self.client.force_login(u)
        self.assertEqual(self.client.get(reverse('core:metricas')).status_code, 404)
