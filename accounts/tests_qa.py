"""QA de formularios (18-10-2026): lo que se vio roto en vivo y la guía de UI/UX."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class FormulariosConElEstiloDelSitio(TestCase):

    def test_el_login_no_sale_con_campos_del_navegador(self):
        """Se veía con la etiqueta pegada al campo y el estilo por defecto."""
        html = self.client.get(reverse('accounts:login')).content.decode()
        self.assertRegex(html, r'<input[^>]*name="username"[^>]*class="form-control"|<input[^>]*class="form-control"[^>]*name="username"')
        self.assertRegex(html, r'autocomplete="current-password"')

    def test_un_error_queda_conectado_a_su_campo(self):
        """Django pone aria-describedby="id_x_error": ese id tiene que existir."""
        user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(user)
        html = self.client.post(reverse('accounts:provider_create'), {'whatsapp_number': '123'}).content.decode()
        self.assertIn('aria-describedby="id_whatsapp_number_error"', html.replace('id_whatsapp_number_helptext ', ''))
        self.assertIn('id="id_whatsapp_number_error"', html)
        self.assertIn('id="errores-form"', html, 'falta el resumen de errores arriba del formulario')
        self.assertIn('href="#id_whatsapp_number"', html)

    def test_los_formularios_se_envian_una_sola_vez(self):
        user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(user)
        self.assertIn('data-un-envio', self.client.get(reverse('accounts:provider_create')).content.decode())


class FirmaGoGoDevS(TestCase):

    def test_el_pie_enlaza_a_gogodevs(self):
        html = self.client.get(reverse('core:home')).content.decode()
        self.assertIn('https://gogodevs.cl/?utm_source=serviplace', html)


class ElFormularioSeAdaptaAlRubro(TestCase):
    """18-10-2026: a un ingeniero en informática le pedía el registro de la
    Superintendencia de Salud y le daba "Kinesióloga" de ejemplo."""

    def setUp(self):
        from io import StringIO
        from django.core.management import call_command
        from directory.models import Region, Commune
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.comuna = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.user = User.objects.create_user('ana', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def test_el_registro_de_salud_se_marca_para_ocultarse_fuera_de_salud(self):
        import json, re
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('data-solo-salud', html)
        info = json.loads(re.search(r'<script id="categorias-info" type="application/json">(.*?)</script>', html, re.S).group(1))
        from directory.models import Category
        self.assertTrue(info[str(Category.objects.get(slug='kinesiologia').pk)]['salud'])
        self.assertFalse(info[str(Category.objects.get(slug='desarrollo-web').pk)]['salud'])

    def test_fuera_de_salud_el_registro_no_se_guarda(self):
        import time
        from django.core import signing
        from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
        from directory.models import Category, Provider
        self.client.post(reverse('accounts:provider_create'), {
            'business_name': 'Diego Pérez, Desarrollo web', 'contact_name': 'Diego Pérez',
            'category': Category.objects.get(slug='desarrollo-web').pk, 'commune': self.comuna.pk, 'sector': 'Centro',
            'short_description': 'Sitios web para pymes.', 'description': 'Sitios web y sistemas a medida.',
            'phone': '+56 9 1111 2222', 'whatsapp_number': '+56 9 1111 2222', 'health_registry': '654321',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        })
        self.assertEqual(Provider.objects.get().health_registry, '')
