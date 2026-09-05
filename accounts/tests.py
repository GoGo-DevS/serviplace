"""Criterios B1, B2, B4 y B5 de TASK.md — seguridad del autoservicio.

POR QUE EXISTE ESTE ARCHIVO
La sesión autónoma del 04-09 escribió el freno de fuerza bruta, el antispam y
la autorización de edición, y **ni una prueba**. Un control de seguridad sin
una prueba que falle al desarmarlo no es un control: es una intención. Este
sitio es autoservicio y abierto a registro público, así que esos controles son
lo único que separa el directorio de un tablón de spam.

CADA PRUEBA DICE QUÉ ATAQUE EVITA, no qué línea ejecuta. Una prueba que
describe la implementación se rompe cuando la implementación cambia aunque el
riesgo siga cubierto; una que describe el riesgo sobrevive al refactor.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD, sello_nuevo
from directory.models import Category, Commune, Provider, Region

from .models import LoginAttempt, UserProfile

User = get_user_model()


def _sello_viejo(segundos=30):
    """Un sello firmado con la antigüedad suficiente para NO parecer un bot."""
    from django.core import signing
    return signing.dumps(timezone.now().timestamp() - segundos)


class Base(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.comuna = Commune.objects.create(region=self.region, name='Maipú',
                                             slug='maipu', is_active=True)
        self.categoria = Category.objects.create(name='Gasfitería', slug='gasfiteria',
                                                 is_active=True)


# ─────────────────────────────────────────────────────────────────────────
# B1 · Fuerza bruta
# ─────────────────────────────────────────────────────────────────────────
@override_settings(LOGIN_MAX_INTENTOS=3, LOGIN_VENTANA_MINUTOS=15)
class B1FrenoDeFuerzaBruta(Base):
    """Sin esto, un registro público con contraseñas de usuarios reales queda
    expuesto a que alguien pruebe миles de claves desde un script."""

    def setUp(self):
        super().setUp()
        User.objects.create_user('vecino', password='clave-larga-de-verdad-99')

    def _fallar(self, veces):
        for _ in range(veces):
            self.client.post(reverse('accounts:login'),
                             {'username': 'vecino', 'password': 'equivocada'})

    def test_al_pasar_el_tope_responde_429(self):
        self._fallar(3)
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'vecino', 'password': 'equivocada'})
        self.assertEqual(r.status_code, 429)

    def test_ANTES_del_tope_el_login_correcto_sigue_funcionando(self):
        """El freno no puede dejar afuera a quien se equivocó una vez. Si esta
        prueba falla, el control es peor que el ataque: bloquea al dueño."""
        self._fallar(2)
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'vecino', 'password': 'clave-larga-de-verdad-99'})
        self.assertNotEqual(r.status_code, 429)
        self.assertIn('_auth_user_id', self.client.session)

    def test_el_bloqueo_mira_la_VENTANA_no_el_total_historico(self):
        """Intentos viejos no pueden bloquear para siempre: con una ventana de
        15 minutos, un fallo de ayer no cuenta hoy."""
        for _ in range(5):
            a = LoginAttempt.objects.create(ip='127.0.0.1', username='vecino')
            LoginAttempt.objects.filter(pk=a.pk).update(
                created_at=timezone.now() - timezone.timedelta(hours=2))
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'vecino', 'password': 'clave-larga-de-verdad-99'})
        self.assertNotEqual(r.status_code, 429)


# ─────────────────────────────────────────────────────────────────────────
# B2 · La contraseña nunca se guarda
# ─────────────────────────────────────────────────────────────────────────
class B2NoSeGuardaLaContrasena(Base):
    """Registrar los intentos fallidos es útil; registrar lo que la gente
    tecleó como contraseña convierte una tabla de auditoría en una filtración.
    Y la gente teclea su contraseña BUENA en el intento fallido: se equivoca de
    usuario, no de clave."""

    def test_ningun_campo_de_LoginAttempt_contiene_la_clave_tecleada(self):
        secreta = 'MiClaveRealDeOtroSitio-2026'
        self.client.post(reverse('accounts:login'),
                         {'username': 'alguien', 'password': secreta})
        intento = LoginAttempt.objects.first()
        self.assertIsNotNone(intento, 'no se registró el intento fallido')
        valores = ' '.join(str(getattr(intento, f.name))
                           for f in LoginAttempt._meta.fields)
        self.assertNotIn(secreta, valores)


# ─────────────────────────────────────────────────────────────────────────
# B4 · Antispam: se marca, NO se rechaza
# ─────────────────────────────────────────────────────────────────────────
class B4AntispamMarcaPeroNoRechaza(Base):
    """La decisión de producto: un sospechoso se GUARDA marcado y sin publicar.

    Rechazarlo convierte cada falso positivo en un prestador real perdido, y
    perdido EN SILENCIO: la persona ve un error, no vuelve, y nadie se entera
    de que existió. Marcado, alguien puede revisarlo después.
    """

    def _registrar(self, **extra):
        datos = {
            'username': 'nuevo', 'email': 'n@example.cl',
            'password1': 'clave-larga-de-verdad-99',
            'password2': 'clave-larga-de-verdad-99',
            TIMESTAMP_FIELD: _sello_viejo(),
            HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return self.client.post(reverse('accounts:register'), datos)

    def test_con_el_honeypot_relleno_el_usuario_SE_CREA_pero_marcado(self):
        # `**{HONEYPOT_FIELD: ...}` y no `HONEYPOT_FIELD=...`: lo segundo pasa
        # el keyword LITERAL "HONEYPOT_FIELD" en vez del nombre real del campo,
        # así que el honeypot quedaba vacío y la prueba fallaba sobre un
        # control que funcionaba bien. Es el modo de fallo más traicionero de
        # una prueba: acusa al código correcto.
        self._registrar(**{HONEYPOT_FIELD: 'http://spam.example'})
        u = User.objects.filter(username='nuevo').first()
        self.assertIsNotNone(u, 'el registro se rechazó en vez de marcarse')
        self.assertTrue(UserProfile.objects.get(user=u).spam_flag)

    def test_rapido_SOLO_no_alcanza_para_marcar_a_nadie(self):
        """Enviar rápido suma 30 y el umbral es 40: por diseño no basta.

        Y está bien que no baste. El autocompletado del navegador llena un
        formulario en menos de un segundo, y marcar por eso solo convertiría a
        cualquiera con las contraseñas guardadas en sospechoso. Hace falta una
        segunda señal.

        Esta prueba fija esa decisión: si alguien baja el umbral a 30, acá se
        entera de que empezó a marcar gente por usar el autocompletado.
        """
        self._registrar(**{TIMESTAMP_FIELD: sello_nuevo()})
        u = User.objects.filter(username='nuevo').first()
        self.assertIsNotNone(u)
        self.assertFalse(UserProfile.objects.get(user=u).spam_flag)

    def test_rapido_MAS_otra_senal_si_marca(self):
        """Dos señales sí: rápido (30) + honeypot (40) pasa el umbral."""
        self._registrar(**{TIMESTAMP_FIELD: sello_nuevo(),
                           HONEYPOT_FIELD: 'http://spam.example'})
        u = User.objects.filter(username='nuevo').first()
        self.assertIsNotNone(u)
        self.assertTrue(UserProfile.objects.get(user=u).spam_flag)

    def test_un_registro_normal_NO_queda_marcado(self):
        """La contracara: si esta prueba falla, el filtro marca a todos y el
        sitio no publica a nadie."""
        self._registrar()
        u = User.objects.get(username='nuevo')
        self.assertFalse(UserProfile.objects.get(user=u).spam_flag)

    def test_lo_marcado_NO_se_publica(self):
        """Marcarlo sin ocultarlo no serviría de nada: el spam igual quedaría
        a la vista del público."""
        u = User.objects.create_user('sospechoso', password='x')
        perfil = UserProfile.objects.get(user=u)
        perfil.spam_flag = True
        perfil.save()
        self.client.force_login(u)
        self.client.post(reverse('accounts:provider_create'), {
            'business_name': 'Gasfitería Dudosa', 'category': self.categoria.pk,
            'commune': self.comuna.pk, 'whatsapp_number': '56911112222',
            'short_description': 'Servicio.', 'description': 'Servicio.',
            TIMESTAMP_FIELD: _sello_viejo(), HONEYPOT_FIELD: '',
        })
        p = Provider.objects.filter(business_name='Gasfitería Dudosa').first()
        if p is not None:
            self.assertFalse(p.is_active, 'un perfil marcado se publicó activo')


# ─────────────────────────────────────────────────────────────────────────
# B5 · Autorización
# ─────────────────────────────────────────────────────────────────────────
class B5NadieEditaElPerfilDeOtro(Base):
    """Con registro abierto, cualquiera puede crear una cuenta. Si la
    autorización se apoyara solo en no mostrar el botón, bastaría escribir la
    URL para cambiarle el teléfono a otro prestador — y el teléfono es
    exactamente lo que este sitio publica."""

    def setUp(self):
        super().setUp()
        self.dueno = User.objects.create_user('dueno', password='x')
        self.ajeno = User.objects.create_user('ajeno', password='x')
        self.perfil = Provider.objects.create(
            business_name='Gasfitería del Dueño', slug='gasfiteria-del-dueno',
            category=self.categoria, commune=self.comuna, owner=self.dueno,
            whatsapp_number='56911112222', is_active=True,
            source_name='Autoservicio', source_url='https://serviplace.cl',
        )

    def test_un_usuario_ajeno_no_puede_abrir_la_edicion(self):
        self.client.force_login(self.ajeno)
        r = self.client.get(reverse('accounts:provider_edit', args=[self.perfil.slug]))
        self.assertIn(r.status_code, (403, 404))

    def test_y_tampoco_puede_cambiarlo_por_POST(self):
        """Lo que de verdad importa: que el POST no escriba. Bloquear el GET y
        dejar pasar el POST es el error clásico."""
        self.client.force_login(self.ajeno)
        self.client.post(reverse('accounts:provider_edit', args=[self.perfil.slug]), {
            'business_name': 'SECUESTRADO', 'category': self.categoria.pk,
            'commune': self.comuna.pk, 'whatsapp_number': '56999999999',
            'short_description': 'x', 'description': 'x',
            TIMESTAMP_FIELD: _sello_viejo(), HONEYPOT_FIELD: '',
        })
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.business_name, 'Gasfitería del Dueño')
        self.assertEqual(self.perfil.whatsapp_number, '56911112222')

    def test_el_dueno_SI_puede_editarlo(self):
        """La contracara: una autorización que bloquea a todos no es segura,
        está rota."""
        self.client.force_login(self.dueno)
        r = self.client.get(reverse('accounts:provider_edit', args=[self.perfil.slug]))
        self.assertEqual(r.status_code, 200)

    def test_un_anonimo_no_llega_a_la_edicion(self):
        r = self.client.get(reverse('accounts:provider_edit', args=[self.perfil.slug]))
        self.assertNotEqual(r.status_code, 200)
