"""Sellos que dicen QUÉ se comprobó (30-10-2026).

Diego quería que los que se inscriben "ya vengan verificados". Un sello
automático que no comprueba nada sería una promesa falsa en el sitio. Lo que
se protege: cada sello lo da staff después de revisar el dato, cambiar el
dato borra el sello, nadie más puede darlos, y confirmar el WhatsApp sube en
los listados (el incentivo).
"""
import time
from io import StringIO
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()
URL = reverse('accounts:comprobaciones')


@override_settings(DEFAULT_CONTACT_WHATSAPP='56911112222')
class Sellos(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = {c.slug: c for c in Category.objects.all()}
        self.dueno = User.objects.create_user('juan', password='clave-larga-de-verdad-99')
        self.staff = User.objects.create_user('diego', password='clave-larga-de-verdad-99', is_staff=True)

    def _perfil(self, nombre='Juan Gásfiter', slug='gasfiteria', **extra):
        return Provider.objects.create(
            owner=self.dueno, business_name=nombre, category=self.cat[slug], commune=self.maipu,
            short_description='Gásfiter en Maipú.', whatsapp_number='56987654321', is_active=True, **extra)

    def _datos(self, p, **extra):
        datos = {
            'business_name': p.business_name, 'contact_name': 'Juan', 'category': p.category_id,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': p.short_description,
            'description': 'Destapes y calefont.', 'phone': '+56 9 8765 4321', 'whatsapp_number': '+56 9 8765 4321',
            'attends_home': 'on',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return datos

    def _dar(self, p, sello, accion=''):
        self.client.force_login(self.staff)
        return self.client.post(URL, {'perfil': p.pk, 'sello': sello, 'accion': accion})

    def test_cada_perfil_tiene_su_codigo_y_su_mensaje_listo(self):
        p = self._perfil()
        self.assertRegex(p.whatsapp_codigo, r'^SP-\d{4}$')
        url = urlparse(p.url_confirmar_whatsapp)
        self.assertEqual(url.netloc + url.path, 'wa.me/56911112222', 'el mensaje va al WhatsApp de ServiPlace')
        self.assertIn(p.whatsapp_codigo, parse_qs(url.query)['text'][0])

    def test_solo_staff_entra_y_da_sellos(self):
        p = self._perfil()
        self.assertEqual(self.client.get(URL).status_code, 302)  # sin sesión: al login
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(URL).status_code, 404)
        self.client.post(URL, {'perfil': p.pk, 'sello': 'whatsapp'})
        p.refresh_from_db()
        self.assertIsNone(p.whatsapp_confirmado_en, 'un no-staff se dio el sello')
        self.client.force_login(self.staff)
        html = self.client.get(URL).content.decode()
        self.assertIn(p.whatsapp_codigo, html)
        self.assertIn('+56 9 8765 4321', html)

    def test_confirmar_el_whatsapp_muestra_el_sello_en_tarjeta_y_ficha(self):
        p = self._perfil()
        listado = reverse('directory:listado_rubro', args=['gasfiteria'])
        self.assertNotIn('WhatsApp confirmado', self.client.get(listado).content.decode())
        self._dar(p, 'whatsapp')
        self.client.logout()
        self.assertIn('WhatsApp confirmado', self.client.get(listado).content.decode())
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('el número es de esta persona', ficha)

    def test_quitar_el_sello(self):
        p = self._perfil()
        self._dar(p, 'whatsapp')
        self._dar(p, 'whatsapp', accion='quitar')
        p.refresh_from_db()
        self.assertIsNone(p.whatsapp_confirmado_en)

    def test_cambiar_el_whatsapp_borra_el_sello_y_el_codigo(self):
        p = self._perfil()
        self._dar(p, 'whatsapp')
        p.refresh_from_db()
        codigo = p.whatsapp_codigo
        self.client.force_login(self.dueno)
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]),
                         self._datos(p, short_description='Gásfiter en Maipú y Cerrillos.'))
        p.refresh_from_db()
        self.assertIsNotNone(p.whatsapp_confirmado_en, 'editar otra cosa no puede borrar el sello')
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]),
                         self._datos(p, whatsapp_number='+56 9 1111 2222'))
        p.refresh_from_db()
        self.assertIsNone(p.whatsapp_confirmado_en, 'lo comprobado era el número anterior')
        self.assertNotEqual(p.whatsapp_codigo, codigo)

    def test_registro_de_salud_comprobado_y_se_borra_si_cambia(self):
        p = self._perfil('Ana Kine', 'kinesiologia', health_registry='123456')
        self._dar(p, 'salud')
        self.assertIn('Registro de salud comprobado', self.client.get(p.get_absolute_url()).content.decode())
        p.refresh_from_db()
        p.health_registry = '999999'
        p.save()
        self.assertFalse(p.registro_salud_comprobado)

    def test_licencia_sec_solo_en_rubros_sec(self):
        self.client.force_login(self.dueno)
        p = self._perfil()
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]), self._datos(p, licencia_sec='Clase 3 gas'))
        p.refresh_from_db()
        self.assertEqual(p.licencia_sec, 'Clase 3 gas')
        pintor = self._perfil('Pinturas Rojas', 'pintura')
        self.client.post(reverse('accounts:provider_edit', args=[pintor.slug]),
                         self._datos(pintor, licencia_sec='Clase D eléctrica'))
        pintor.refresh_from_db()
        self.assertEqual(pintor.licencia_sec, '', 'un pintor no tiene licencia SEC que comprobar')
        self._dar(p, 'sec')
        p.refresh_from_db()
        self.assertTrue(p.licencia_sec_comprobada)

    def test_con_whatsapp_confirmado_sale_antes(self):
        primero = self._perfil('Aaa Gásfiter')
        segundo = self._perfil('Zzz Gásfiter')
        listado = reverse('directory:listado_rubro', args=['gasfiteria'])
        nombres = [p.business_name for p in self.client.get(listado).context['providers']]
        self.assertEqual(nombres, ['Aaa Gásfiter', 'Zzz Gásfiter'])
        Provider.objects.filter(pk=segundo.pk).update(whatsapp_confirmado_en=timezone.now())
        nombres = [p.business_name for p in self.client.get(listado).context['providers']]
        self.assertEqual(nombres, ['Zzz Gásfiter', 'Aaa Gásfiter'])
        self.assertTrue(primero.pk)

    def test_el_dueno_ve_como_confirmar_y_el_visitante_no(self):
        p = self._perfil()
        self.client.force_login(self.dueno)
        self.assertIn('Confirmar mi WhatsApp', self.client.get(reverse('accounts:dashboard')).content.decode())
        self.assertIn('Confirmar mi WhatsApp', self.client.get(p.get_absolute_url()).content.decode())
        self.client.logout()
        self.assertNotIn('Confirmar mi WhatsApp', self.client.get(p.get_absolute_url()).content.decode())

    def test_seguridad_explica_cada_sello(self):
        html = self.client.get(reverse('core:trust_and_safety')).content.decode()
        for sello in ('WhatsApp confirmado', 'Registro de salud comprobado', 'Licencia SEC comprobada'):
            self.assertIn(sello, html)

    def _texto_hazte_verificado(self):
        url = self.client.get(reverse('accounts:hazte_verificado')).context['wa_url']
        self.assertTrue(url.startswith('https://wa.me/56911112222?'))
        return parse_qs(urlparse(url).query)['text'][0]

    def test_hazte_verificado_dice_que_perfil_es_y_lleva_su_codigo(self):
        # 02-11-2026: llegó "quiero verificar mi perfil" sin decir cuál, y sin
        # código no había cómo confirmar el WhatsApp con ese mismo mensaje.
        p = self._perfil('Midnight Studio')
        self.client.force_login(self.dueno)
        texto = self._texto_hazte_verificado()
        self.assertIn('Midnight Studio', texto)
        self.assertIn(p.get_absolute_url(), texto)
        self.assertIn(f'Código: {p.whatsapp_codigo}', texto)

    def test_hazte_verificado_sin_perfil_pide_los_datos_como_antes(self):
        self.assertEqual(self._texto_hazte_verificado(), 'Hola, quiero verificar mi perfil en ServiPlace.')
        self.client.force_login(self.dueno)  # con cuenta pero sin perfil publicado
        self.assertEqual(self._texto_hazte_verificado(), 'Hola, quiero verificar mi perfil en ServiPlace.')
