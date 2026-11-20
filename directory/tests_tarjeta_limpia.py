"""La tarjeta "clean" (20-11-2026, Diego con capturas de la tarjeta del gásfiter):

- Sin "Ver ficha →": toda la tarjeta lleva a la ficha (el enlace del nombre se estira).
- Sin "Verificado por ServiPlace" escrito: lo dice el visto azul junto al nombre.
- Modalidades (a domicilio, local, online) en íconos; el texto queda para lectores de pantalla.
- El rubro con su ícono.
- Logo de la institución donde estudió, si lo tenemos; si no, el nombre como siempre.
- Lo que SÍ se sigue avisando: cuando los datos no los publicó la persona.
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from directory.models import Category, Commune, Provider, Region
from directory.templatetags.rubros import clave_institucion, logo_institucion

User = get_user_model()


class TarjetaLimpia(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.gas = Category.objects.get(slug='gasfiteria')

    def _perfil(self, nombre, dueno=True, **extra):
        owner = User.objects.create_user(nombre.split()[0].lower(), password='clave-larga-de-verdad-99') if dueno else None
        return Provider.objects.create(
            owner=owner, business_name=nombre, category=self.gas, commune=self.maipu, sector='Maipú',
            short_description='Gasfitería y calefont.', whatsapp_number='56987654321', is_active=True, **extra)

    def _tarjeta(self, nombre):
        html = self.client.get(reverse('directory:listado_rubro', args=['gasfiteria'])).content.decode()
        # El nombre también sale antes, en el JSON-LD de la cabecera: se busca desde la primera tarjeta.
        i = html.index(nombre, html.index('<article class="ficha"'))
        return html[html.rindex('<article class="ficha"', 0, i):html.index('</article>', i)]

    def test_la_tarjeta_entera_lleva_a_la_ficha_sin_ver_ficha_ni_verificado_escrito(self):
        p = self._perfil('Rodrigo Saavedra', is_verified=True, whatsapp_confirmado_en=timezone.now())
        t = self._tarjeta('Rodrigo Saavedra')
        self.assertIn(f'class="ficha-link" href="{p.get_absolute_url()}"', t)
        self.assertNotIn('Ver ficha', t)
        self.assertNotIn('ficha-estado', t)          # el visto azul ya dice que está verificado
        self.assertIn('data-check-verificado', t)
        self.assertIn('btn btn-success', t)          # WhatsApp sigue siendo su propio botón

    def test_las_modalidades_son_iconos_con_texto_para_lectores_de_pantalla(self):
        self._perfil('Gásfiter Pérez', attends_home=True, attends_online=True)
        t = self._tarjeta('Gásfiter Pérez')
        self.assertEqual(t.count('class="modal-ico"'), 2)
        self.assertIn('<span class="visually-hidden">A domicilio</span>', t)
        self.assertIn('<span class="visually-hidden">Online</span>', t)
        self.assertNotIn('mini-pill', t)

    def test_el_rubro_lleva_su_icono(self):
        self._perfil('Gásfiter Soto')
        t = self._tarjeta('Gásfiter Soto')
        top = t[t.index('ficha-top'):t.index('</div>', t.index('ficha-top'))]
        self.assertIn('ico-rubro', top)
        self.assertIn('Gasfitería', top)

    def test_si_no_lo_publico_la_persona_se_sigue_avisando(self):
        # Los clientes de GoGoDevS se cargan desde su sitio: no los publicó el dueño en persona.
        # (Un perfil sin dueño no llega a ningún listado público desde el 18-10.)
        self._perfil('Gasfitería del Sitio', source_name='cliente-gogodevs')
        self.assertIn('Datos de su sitio web oficial', self._tarjeta('Gasfitería del Sitio'))

    def test_publicado_por_su_dueno_ya_no_se_escribe(self):
        self.assertNotIn('Publicado por su dueño', self._tarjeta(self._perfil('Gásfiter Rojas').business_name))


class LogoDeLaInstitucion(TestCase):

    def test_reconoce_la_institucion_aunque_este_escrita_a_mano(self):
        casos = {
            'INACAP sede Maipú': 'inacap', 'Instituto Profesional Duoc UC': 'duoc', 'duoc': 'duoc',
            'Universidad de Chile': 'uchile', 'USACH': 'usach', 'Universidad de Santiago de Chile': 'usach',
            'Pontificia Universidad Católica de Chile': 'uc', 'Universidad de Concepción': 'udec',
            'Universidad Técnica Federico Santa María': 'utfsm', 'Liceo Santa María de Maipú': '',
            'Escuela de oficios municipal': '', '': '',
        }
        for nombre, clave in casos.items():
            self.assertEqual(clave_institucion(nombre), clave, nombre)

    def test_sin_el_archivo_del_logo_no_se_dibuja_nada(self):
        self.assertEqual(logo_institucion('Escuela de oficios municipal'), '')


class SellosSegunElRubro(TestCase):
    """20-11-2026, Diego: "un informático no puede tener una certificación SEC, lo mismo
    con los de la salud". El sello sale solo si alguno de los rubros del perfil lo pide."""

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.n = 0

    def _perfil(self, rubro, **extra):
        self.n += 1
        return Provider.objects.create(
            owner=User.objects.create_user(f'p{self.n}', password='clave-larga-de-verdad-99'),
            business_name=f'Perfil {self.n}', category=Category.objects.get(slug=rubro), commune=self.maipu,
            sector='Maipú', short_description='Servicio.', whatsapp_number='56987654321', is_active=True, **extra)

    def _sec(self, rubro):
        return self._perfil(rubro, licencia_sec='Clase D eléctrica', licencia_sec_comprobada_en=timezone.now())

    def _salud(self, rubro):
        return self._perfil(rubro, health_registry='123456', registro_salud_comprobado_en=timezone.now())

    def test_un_informatico_con_licencia_cargada_no_muestra_la_sec(self):
        p = self._sec('desarrollo-web')
        self.assertFalse(p.licencia_sec_comprobada)
        self.assertNotIn('data-sello="sec"', self.client.get(p.get_absolute_url()).content.decode())

    def test_un_gasfiter_si_la_muestra(self):
        p = self._sec('gasfiteria')
        self.assertTrue(p.licencia_sec_comprobada)
        self.assertIn('data-sello="sec"', self.client.get(p.get_absolute_url()).content.decode())

    def test_si_la_pide_uno_de_sus_otros_rubros_tambien(self):
        p = self._sec('desarrollo-web')
        p.otras_categorias.add(Category.objects.get(slug='electricidad'))
        self.assertTrue(Provider.objects.get(pk=p.pk).licencia_sec_comprobada)

    def test_un_gasfiter_con_registro_de_salud_cargado_no_muestra_el_sello_de_salud(self):
        p = self._salud('gasfiteria')
        self.assertFalse(p.registro_salud_comprobado)
        self.assertNotIn('data-sello="salud"', self.client.get(p.get_absolute_url()).content.decode())

    def test_una_kine_si_lo_muestra(self):
        p = self._salud('kinesiologia')
        self.assertTrue(p.registro_salud_comprobado)
        self.assertIn('data-sello="salud"', self.client.get(p.get_absolute_url()).content.decode())
