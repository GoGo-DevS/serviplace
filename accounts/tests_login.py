"""Entrar con el usuario o con el correo, y cómo recuperar la clave (11-11-2026).

Manitos Curiosas no pudo entrar: el login pedía "Nombre de usuario", ella
escribía lo que recordaba y no había "¿Olvidaste tu contraseña?". Lo que se
protege: que el correo y el usuario con otras mayúsculas sirvan, que una clave
mala o una cuenta desactivada sigan sin entrar, y que haya un camino visible
para recuperar la clave.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()
CLAVE = 'clave-larga-de-verdad-99'


class EntrarConUsuarioOCorreo(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('ManitosCuriosas', email='hola@manitoscuriosas.cl', password=CLAVE)

    def _entrar(self, usuario, clave=CLAVE):
        self.client.logout()
        return self.client.post(reverse('accounts:login'), {'username': usuario, 'password': clave})

    def _adentro(self):
        return self.client.session.get('_auth_user_id') == str(self.user.pk)

    def test_entra_con_el_correo(self):
        self._entrar('hola@manitoscuriosas.cl')
        self.assertTrue(self._adentro())

    def test_entra_con_el_correo_o_el_usuario_sin_importar_mayusculas(self):
        for usuario in ('HOLA@ManitosCuriosas.cl', 'manitoscuriosas', ' ManitosCuriosas '):
            self._entrar(usuario)
            self.assertTrue(self._adentro(), usuario)

    def test_con_la_clave_mala_no_entra_y_el_aviso_dice_que_sirve_el_correo(self):
        respuesta = self._entrar('hola@manitoscuriosas.cl', 'otra-clave-cualquiera-1')
        self.assertFalse(self._adentro())
        self.assertContains(respuesta, 'Puedes entrar con tu correo')

    def test_una_cuenta_desactivada_no_entra(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self._entrar('hola@manitoscuriosas.cl')
        self.assertFalse(self._adentro())

    def test_correo_repetido_entra_a_la_cuenta_cuya_clave_calza(self):
        otra = User.objects.create_user('otra-cuenta', email='hola@manitoscuriosas.cl', password='la-clave-de-la-otra-77')
        self._entrar('hola@manitoscuriosas.cl', 'la-clave-de-la-otra-77')
        self.assertEqual(self.client.session.get('_auth_user_id'), str(otra.pk))

    def test_la_etiqueta_dice_usuario_o_correo(self):
        self.assertContains(self.client.get(reverse('accounts:login')), 'Usuario o correo')

    @override_settings(DEFAULT_CONTACT_WHATSAPP='56911112222')
    def test_hay_como_recuperar_la_clave(self):
        html = self.client.get(reverse('accounts:login')).content.decode()
        self.assertIn('¿Olvidaste tu contraseña?', html)
        self.assertIn('href="https://wa.me/56911112222?text=Hola%2C%20olvid%C3%A9%20mi%20contrase%C3%B1a', html)

    @override_settings(DEFAULT_CONTACT_WHATSAPP='')
    def test_sin_numero_no_queda_un_enlace_roto(self):
        self.assertNotContains(self.client.get(reverse('accounts:login')), 'data-olvide-clave')
