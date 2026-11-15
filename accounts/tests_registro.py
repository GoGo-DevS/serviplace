"""El registro corto y el 403 de CSRF con salida (15-11-2026).

De 172 personas que abrieron el registro en 30 días, 26 crearon la cuenta. Y
en los registros de Render había "POST /cuenta/registro/ 403": la página de
Django en inglés, que a quien acababa de crear la cuenta le decía que no.
"""
import time

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import Client, TestCase
from django.urls import reverse

from accounts.forms import RegisterForm
from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()
CLAVE = 'una-clave-larga-99'


def sello():
    return signing.dumps(int(time.time()) - 60, salt='antispam')


def datos_registro(**extra):
    datos = {'email': 'tomas.rojas@example.cl', 'password1': CLAVE,
             TIMESTAMP_FIELD: sello(), HONEYPOT_FIELD: ''}
    datos.update(extra)
    return datos


def ficha_de(user):
    region = Region.objects.create(name='RM', slug='rm', is_active=True)
    comuna = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
    rubro = Category.objects.create(name='Gasfitería', slug='gasfiteria')
    return Provider.objects.create(owner=user, business_name='Gasfitería Rojas', contact_name='Tomás',
                                   category=rubro, commune=comuna, short_description='Gásfiter',
                                   description='Destapes', phone='+56987654321')


class ElRegistroPideSoloCorreoYContrasena(TestCase):
    def test_con_correo_y_una_contrasena_crea_la_cuenta_y_sigue_al_paso_2(self):
        respuesta = self.client.post(reverse('accounts:register'), datos_registro())
        self.assertRedirects(respuesta, reverse('accounts:provider_create'), fetch_redirect_response=False)
        user = User.objects.get(email='tomas.rojas@example.cl')
        self.assertEqual(user.username, 'tomas.rojas')
        self.assertTrue(user.check_password(CLAVE))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_el_usuario_que_sale_del_correo_no_choca_con_uno_que_ya_existe(self):
        User.objects.create_user('Tomas.Rojas', password=CLAVE)  # mayúsculas: el chequeo es sin distinguirlas
        User.objects.create_user('tomas.rojas2', password=CLAVE)
        self.client.post(reverse('accounts:register'), datos_registro())
        self.assertEqual(User.objects.get(email='tomas.rojas@example.cl').username, 'tomas.rojas3')

    def test_un_correo_con_tildes_o_signos_da_un_usuario_valido(self):
        self.assertEqual(RegisterForm.usuario_desde_correo('José.Muñoz+obra@gmail.com'), 'jose.munoz')
        self.assertEqual(RegisterForm.usuario_desde_correo('___@x.cl'), 'usuario')
        # (Un correo con tildes antes de la @ no pasa el EmailField de Django.)
        respuesta = self.client.post(reverse('accounts:register'), datos_registro(email='Ana.Maria_Soto@example.cl'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(User.objects.filter(username='ana.maria_soto').exists())

    def test_una_contrasena_debil_se_avisa_en_el_campo_que_la_persona_ve(self):
        respuesta = self.client.post(reverse('accounts:register'), datos_registro(password1='12345678'))
        self.assertEqual(respuesta.status_code, 200)
        form = respuesta.context['form']
        self.assertIn('password1', form.errors)
        self.assertNotIn('password2', form.errors)  # password2 ya no se dibuja: un error ahí no se vería
        self.assertFalse(User.objects.filter(email='tomas.rojas@example.cl').exists())

    def test_sin_contrasena_no_crea_nada_y_lo_dice(self):
        respuesta = self.client.post(reverse('accounts:register'), datos_registro(password1=''))
        self.assertIn('password1', respuesta.context['form'].errors)
        self.assertFalse(User.objects.exists())

    def test_el_formulario_viejo_con_usuario_y_dos_contrasenas_sigue_funcionando(self):
        respuesta = self.client.post(reverse('accounts:register'), datos_registro(
            username='camila', password2=CLAVE))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(User.objects.filter(username='camila').exists())

    def test_dos_contrasenas_distintas_siguen_rechazandose(self):
        respuesta = self.client.post(reverse('accounts:register'), datos_registro(password2='otra-clave-larga-77'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_la_pagina_no_dibuja_usuario_ni_confirmacion_ni_cv(self):
        html = self.client.get(reverse('accounts:register')).content.decode()
        for campo in ('name="email"', 'name="password1"', 'name="whatsapp"'):
            self.assertIn(campo, html)
        for campo in ('name="username"', 'name="password2"', 'name="cv"'):
            self.assertNotIn(campo, html)
        self.assertIn('data-ver-clave', html)          # botón para ver la contraseña
        self.assertIn('data-recargar-si-vuelve', html)  # se recarga si vuelve con "atrás"

    def test_la_pagina_dice_lo_que_se_lleva_y_como_sigue(self):
        html = self.client.get(reverse('accounts:register')).content.decode()
        for texto in ('Paso 1 de 2', 'Gratis y sin comisión', 'directo a tu WhatsApp', 'comunas',
                      'historia lista', 'al instante', 'tu CV'):
            self.assertIn(texto, html)

    def test_la_pagina_no_se_guarda_en_cache(self):
        respuesta = self.client.get(reverse('accounts:register'))
        self.assertIn('no-store', respuesta['Cache-Control'])


class ConLaCuentaYaCreada(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tomas', email='t@example.cl', password=CLAVE)
        self.client.force_login(self.user)

    def test_sin_ficha_volver_al_registro_lleva_al_paso_2(self):
        respuesta = self.client.get(reverse('accounts:register'))
        self.assertRedirects(respuesta, reverse('accounts:provider_create'), fetch_redirect_response=False)

    def test_con_ficha_volver_al_registro_lleva_al_panel(self):
        ficha_de(self.user)
        respuesta = self.client.get(reverse('accounts:register'))
        self.assertRedirects(respuesta, reverse('accounts:dashboard'), fetch_redirect_response=False)


class El403DeCSRFTieneSalida(TestCase):
    """Con `enforce_csrf_checks` el cliente de pruebas se comporta como un
    navegador: sin token válido, Django llama a CSRF_FAILURE_VIEW."""

    def setUp(self):
        self.navegador = Client(enforce_csrf_checks=True)

    def test_registrarse_con_la_pagina_vencida_y_la_sesion_ya_iniciada_sigue_al_paso_2(self):
        # El caso de los logs: la cuenta se creó (y la sesión se inició, lo que
        # cambia el token), y la página vieja reenvía el formulario.
        user = User.objects.create_user('tomas', email='t@example.cl', password=CLAVE)
        self.navegador.force_login(user)
        with self.assertLogs('serviplace.csrf', 'WARNING') as logs:
            respuesta = self.navegador.post(reverse('accounts:register'), datos_registro())
        self.assertRedirects(respuesta, reverse('accounts:provider_create'), fetch_redirect_response=False)
        self.assertIn('/cuenta/registro/', logs.output[0])
        self.assertIn('sesion=True', logs.output[0])
        seguir = self.navegador.get(reverse('accounts:provider_create'))
        self.assertContains(seguir, 'Tu cuenta ya quedó creada')
        self.assertEqual(User.objects.count(), 1)

    def test_con_ficha_publicada_lleva_al_panel(self):
        user = User.objects.create_user('tomas', email='t@example.cl', password=CLAVE)
        ficha_de(user)
        self.navegador.force_login(user)
        with self.assertLogs('serviplace.csrf', 'WARNING'):
            respuesta = self.navegador.post(reverse('accounts:register'), datos_registro())
        self.assertRedirects(respuesta, reverse('accounts:dashboard'), fetch_redirect_response=False)

    def test_sin_cuenta_devuelve_el_formulario_con_el_correo_y_un_token_nuevo(self):
        with self.assertLogs('serviplace.csrf', 'WARNING') as logs:
            respuesta = self.navegador.post(reverse('accounts:register'), datos_registro(whatsapp='+56 9 8765 4321'))
        self.assertEqual(respuesta.status_code, 403)
        html = respuesta.content.decode()
        self.assertIn('La página se había quedado desactualizada', html)
        self.assertIn('value="tomas.rojas@example.cl"', html)
        self.assertIn('value="+56 9 8765 4321"', html)
        self.assertNotIn(CLAVE, html)                    # la contraseña no vuelve a la página
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('sin_cookies=True', logs.output[0])  # el cliente no mandó ninguna cookie
        self.assertIn('Abrir en el navegador', html)
        self.assertRegex(html, r'<input[^>]*name="password1"[^>]*autofocus')  # el cursor, donde falta escribir
        self.assertNotRegex(html, r'<input[^>]*name="email"[^>]*autofocus')
        self.assertFalse(User.objects.exists())          # sin token válido no se guarda nada

    def test_reenviar_desde_esa_pagina_crea_la_cuenta(self):
        with self.assertLogs('serviplace.csrf', 'WARNING'):
            respuesta = self.navegador.post(reverse('accounts:register'), datos_registro())
        token = respuesta.context['csrf_token']
        respuesta = self.navegador.post(reverse('accounts:register'),
                                        datos_registro(csrfmiddlewaretoken=str(token)))
        self.assertRedirects(respuesta, reverse('accounts:provider_create'), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email='tomas.rojas@example.cl').exists())

    def test_en_otra_pagina_explica_en_castellano_sin_el_ingles_de_django(self):
        with self.assertLogs('serviplace.csrf', 'WARNING'):
            respuesta = self.navegador.post(reverse('core:contact'), {'nombre': 'x'})
        self.assertEqual(respuesta.status_code, 403)
        html = respuesta.content.decode()
        self.assertIn('No pudimos guardar lo que enviaste', html)
        self.assertIn('recarga la página', html)
        self.assertNotIn('CSRF verification failed', html)
