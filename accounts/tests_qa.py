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
