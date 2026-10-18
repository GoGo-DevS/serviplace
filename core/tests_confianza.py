"""SEO técnico y confianza, tanda nocturna del 18-10-2026.

Cada prueba sale de un hallazgo medido en el sitio en vivo o en Lighthouse:
el hostname de Render servía una copia del sitio, el primer pintado esperaba
a tres servidores ajenos, no había política de privacidad aunque GA4 la exige,
y la página de contacto prometía WhatsApp y correo sin tener ninguno.
"""
import re
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import LoginAttempt
from directory.models import Commune, Region

User = get_user_model()

RENDER = dict(SITE_URL='https://serviplace.cl', RENDER_EXTERNAL_HOSTNAME='serviplace-60so.onrender.com',
              ALLOWED_HOSTS=['serviplace.cl', 'serviplace-60so.onrender.com', 'testserver'])


class UnSoloDominio(TestCase):

    @override_settings(**RENDER)
    def test_el_hostname_de_render_redirige_al_dominio_con_el_mismo_path(self):
        r = self.client.get('/profesionales/?desde=x', HTTP_HOST='serviplace-60so.onrender.com')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], 'https://serviplace.cl/profesionales/?desde=x')

    @override_settings(**RENDER)
    def test_el_dominio_propio_no_se_redirige(self):
        self.assertEqual(self.client.get('/profesionales/', HTTP_HOST='serviplace.cl').status_code, 200)

    def test_sin_render_no_hace_nada(self):
        self.assertEqual(self.client.get('/profesionales/').status_code, 200)


class NadaDeTercerosAntesDelPrimerPintado(TestCase):

    def test_bootstrap_y_las_fuentes_vienen_del_propio_sitio(self):
        html = self.client.get('/').content.decode()
        self.assertNotIn('fonts.googleapis.com', html)
        self.assertNotIn('cdn.jsdelivr.net', html)
        self.assertIn('vendor/bootstrap/bootstrap.min.css', html)
        self.assertIn('css/fuentes.css', html)
        self.assertRegex(html, r'<link rel="preload" href="[^"]+bricolage[^"]+\.woff2" as="font" type="font/woff2" crossorigin>')

    def test_el_js_de_bootstrap_no_bloquea(self):
        html = self.client.get('/').content.decode()
        self.assertRegex(html, r'<script src="[^"]+bootstrap\.bundle\.min\.js" defer></script>')


class Privacidad(TestCase):

    def test_existe_y_explica_google_analytics_y_como_evitarlo(self):
        html = self.client.get(reverse('core:privacy')).content.decode()
        self.assertIn('Google Analytics', html)
        self.assertIn('tools.google.com/dlpage/gaoptout', html)
        self.assertIn('no guardamos el archivo', html)

    def test_esta_enlazada_en_el_pie_y_en_el_registro(self):
        url = reverse('core:privacy')
        self.assertIn(f'href="{url}"', self.client.get('/').content.decode())
        self.assertIn(f'href="{url}"', self.client.get(reverse('accounts:register')).content.decode())

    def test_esta_en_el_sitemap(self):
        self.assertIn('/privacidad/</loc>', self.client.get('/sitemap.xml').content.decode())


class Contacto(TestCase):

    @override_settings(DEFAULT_CONTACT_WHATSAPP='56911112222')
    def test_tiene_canales_reales_con_el_mensaje_armado(self):
        html = self.client.get(reverse('core:contact')).content.decode()
        self.assertIn('https://wa.me/56911112222?text=Hola%2C+quiero+publicar', html)
        self.assertGreaterEqual(html.count('https://wa.me/56911112222'), 4)

    @override_settings(DEFAULT_CONTACT_WHATSAPP='56911112222')
    def test_no_se_cuenta_como_contacto_a_un_profesional(self):
        """contacto_whatsapp es el evento que el reporte del CRM suma como
        "alguien le escribió a un profesional". Escribirle a ServiPlace no lo es."""
        html = self.client.get(reverse('core:contact')).content.decode()
        self.assertNotIn('data-ga="contacto_whatsapp"', html)
        self.assertIn('data-ga="contacto_serviplace"', html)

    def test_no_promete_un_correo_que_no_existe(self):
        html = self.client.get(reverse('core:contact')).content.decode()
        self.assertNotIn('o correo', html)


class LosIntentosDeLoginNoSeGuardanParaSiempre(TestCase):

    def test_a_los_30_dias_se_borran(self):
        viejo = LoginAttempt.objects.create(ip='10.0.0.1', username='alguien')
        LoginAttempt.objects.filter(pk=viejo.pk).update(created_at=timezone.now() - timezone.timedelta(days=31))
        reciente = LoginAttempt.objects.create(ip='10.0.0.2', username='otra')
        self.client.post(reverse('accounts:login'), {'username': 'nadie', 'password': 'mala'})
        self.assertFalse(LoginAttempt.objects.filter(pk=viejo.pk).exists())
        self.assertTrue(LoginAttempt.objects.filter(pk=reciente.pk).exists())
        self.assertTrue(LoginAttempt.objects.filter(username='nadie').exists(), 'el fallo nuevo sí se cuenta')


class OrdenDeTitulos(TestCase):
    """Un h3 antes de cualquier h2 confunde a los lectores de pantalla y a
    Google al leer la estructura (Lighthouse lo marcó en /profesionales/)."""

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())

    def test_ningun_titulo_salta_un_nivel(self):
        for url in ('/', '/profesionales/', reverse('core:privacy'), reverse('core:contact'),
                    reverse('core:about'), reverse('core:terms'), reverse('core:trust_and_safety')):
            html = self.client.get(url).content.decode()
            main = html.split('<main', 1)[1].split('</main>', 1)[0]
            niveles = [int(n) for n in re.findall(r'<h([1-6])\b', main)]
            self.assertEqual(niveles[:1], [1], f'{url}: debe partir con un h1')
            self.assertEqual(niveles.count(1), 1, f'{url}: un solo h1')
            for antes, despues in zip(niveles, niveles[1:]):
                self.assertLessEqual(despues - antes, 1, f'{url}: salta de h{antes} a h{despues}')


class EntidadDeMarca(TestCase):
    """El sitio y la cuenta de Instagram se declaran la misma entidad, en los
    dos sentidos: sameAs en el schema y enlace visible en el pie."""

    def test_instagram_en_el_schema_y_en_el_pie(self):
        import json
        html = self.client.get('/').content.decode()
        bloques = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
        org = next(n for b in bloques for n in b.get('@graph', []) if n.get('@type') == 'Organization')
        self.assertIn('https://www.instagram.com/serviplace.cl/', org['sameAs'])
        self.assertIn('href="https://www.instagram.com/serviplace.cl/"', html)
