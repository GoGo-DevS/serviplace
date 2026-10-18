"""/links/ — el enlace de la bio de Instagram (18-10-2026).

Lo que se protege: que lleve a buscar y a publicar, que no ofrezca rubros
vacíos (un listado sin nadie es lo primero que vería quien llega de IG), que
cada botón se mida con tree_click, y que no compita con la portada en Google.
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from directory.models import Category, Commune, Provider, Region
from leads.models import LeadEvent

User = get_user_model()


class LinksDeInstagram(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        dueno = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        Provider.objects.create(
            owner=dueno, business_name='Gasfitería Camila', category=Category.objects.get(slug='gasfiteria'),
            commune=self.maipu, short_description='Gásfiter en Maipú.', whatsapp_number='+56987654321',
            is_active=True)

    def _html(self):
        r = self.client.get(reverse('core:links'))
        self.assertEqual(r.status_code, 200)
        return r.content.decode()

    def test_lleva_a_buscar_y_a_publicar(self):
        html = self._html()
        self.assertEqual(reverse('core:links'), '/links/')
        self.assertIn(f'href="{reverse("directory:provider_list")}"', html)
        self.assertIn(f'href="{reverse("core:para_profesionales")}"', html)
        self.assertIn(f'href="{reverse("core:guias")}"', html)
        self.assertIn('https://www.instagram.com/serviplace.cl/', html)

    def test_solo_ofrece_rubros_con_perfiles(self):
        html = self._html()
        hogar = Category.GROUP_SLUGS[Category.HOGAR]
        salud = Category.GROUP_SLUGS[Category.SALUD]
        self.assertIn(reverse('directory:listado_rubro', args=[hogar]), html)
        self.assertNotIn(reverse('directory:listado_rubro', args=[salud]), html,
                         'ofrece un rubro sin un solo perfil publicado')
        self.assertIn('1 perfil publicado por sus dueños', html)

    def test_cada_boton_se_mide_con_tree_click(self):
        html = self._html()
        self.assertIn("gtag('event', 'tree_click'", html)
        self.assertIn('destino', html)
        self.assertIn('texto_boton', html)
        self.assertGreaterEqual(html.count('data-tree'), 6)

    @override_settings(DEFAULT_CONTACT_WHATSAPP='56911112222')
    def test_whatsapp_de_contacto_cuando_hay_numero(self):
        self.assertIn('https://wa.me/56911112222?text=', self._html())

    @override_settings(DEFAULT_CONTACT_WHATSAPP='')
    def test_sin_numero_no_hay_boton_de_whatsapp_roto(self):
        self.assertNotIn('wa.me/', self._html())

    def test_va_sin_menu_ni_pie_y_no_compite_en_google(self):
        html = self._html()
        self.assertNotIn('site-navbar', html)
        self.assertNotIn('site-footer', html)
        self.assertNotIn('ig-flotante', html)
        self.assertIn('<meta name="robots" content="noindex, follow">', html)
        self.assertNotIn('/links/', self.client.get('/sitemap.xml').content.decode())
        # El resto del sitio sigue con su menú y su pie.
        portada = self.client.get(reverse('core:home')).content.decode()
        self.assertIn('site-navbar', portada)
        self.assertIn('site-footer', portada)

    def test_la_visita_queda_en_las_metricas_internas(self):
        # Sin user-agent cuenta como bot y no se anota: entra como un iPhone desde Instagram.
        self.client.get(reverse('core:links'), HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Instagram 300.0')
        self.assertTrue(LeadEvent.objects.filter(event_type=LeadEvent.PAGE_VIEW, source_page='links').exists())
