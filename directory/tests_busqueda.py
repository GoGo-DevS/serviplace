"""La búsqueda entiende oficios y los rubros que faltaban (20-10-2026).

"fotógrafo", "diseñador", "informático", "gasfiter" sin tilde: la búsqueda
comparaba con el nombre del rubro y con tildes exactas, y daba cero aunque
hubiera perfiles. Diego además echó en falta editor de video, eventos y
marketing/relaciones públicas.
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from directory.busqueda import rubros_de_la_busqueda
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class BusquedaPorOficio(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = {c.slug: c for c in Category.objects.all()}
        self.dueno = User.objects.create_user('dueno', password='clave-larga-de-verdad-99')

    def _perfil(self, nombre, slug, otras=(), descripcion='Trabajo en Maipú.'):
        p = Provider.objects.create(
            owner=self.dueno, business_name=nombre, category=self.cat[slug], commune=self.maipu,
            short_description=descripcion, description=descripcion, whatsapp_number='+56987654321', is_active=True)
        p.otras_categorias.set([self.cat[s] for s in otras])
        return p

    def _nombres(self, q):
        r = self.client.get(reverse('directory:provider_list'), {'q': q})
        return {p.business_name for p in r.context['providers']}

    def test_la_gente_busca_el_oficio_no_el_nombre_del_rubro(self):
        self._perfil('Ana Fotos', 'fotografia-y-video')
        self._perfil('Pedro Diseño', 'diseno-grafico')
        self._perfil('Juan Gas', 'gasfiteria')
        self._perfil('Luis PC', 'soporte-computacional')
        self._perfil('Marta Ley', 'asesoria-legal')
        casos = {
            'fotógrafo': 'Ana Fotos', 'Fotógrafas': 'Ana Fotos', 'fotografos maipu': 'Ana Fotos',
            'diseñador': 'Pedro Diseño', 'disenadora grafica': 'Pedro Diseño',
            'gasfiter': 'Juan Gas', 'Gásfiter': 'Juan Gas',
            'informático': 'Luis PC', 'abogada de familia': 'Marta Ley',
        }
        for q, esperado in casos.items():
            self.assertIn(esperado, self._nombres(q), q)

    def test_tambien_por_un_rubro_extra(self):
        self._perfil('Maestro Juan', 'construccion', otras=['gasfiteria', 'soldadura'])
        self.assertEqual(self._nombres('soldador'), {'Maestro Juan'})
        self.assertEqual(self._nombres('gasfiter'), {'Maestro Juan'})

    def test_no_mezcla_oficios(self):
        self._perfil('Ana Fotos', 'fotografia-y-video')
        self._perfil('Pinturas Rojas', 'pintura')
        self.assertEqual(self._nombres('fotógrafo'), {'Ana Fotos'})
        self.assertEqual(self._nombres('pintor'), {'Pinturas Rojas'})
        self.assertEqual(self._nombres('zzzzqq'), set())
        self.assertEqual(rubros_de_la_busqueda('automatización'), [],
                         '"auto" es de mecánica: no puede calzar dentro de otra palabra')

    def test_los_rubros_que_faltaban_existen_y_se_encuentran(self):
        nuevos = {'edicion-de-video': 'editor de video', 'produccion-de-eventos': 'organizar un matrimonio',
                  'marketing-y-rrpp': 'community manager', 'asesoria-legal': 'abogado',
                  'arquitectura': 'arquitecto', 'traduccion': 'traductora',
                  'mecanica-automotriz': 'mecánico', 'entrenamiento-personal': 'personal trainer'}
        for slug, busqueda in nuevos.items():
            self.assertIn(slug, self.cat, f'falta el rubro {slug}')
            self.assertIn(self.cat[slug].pk, rubros_de_la_busqueda(busqueda), busqueda)
            self.assertEqual(self.client.get(reverse('core:profesion', args=[slug])).status_code, 200, slug)
        self.assertEqual(self.cat['marketing-y-rrpp'].group, Category.PROFESIONAL)
        self.assertFalse(self.cat['entrenamiento-personal'].pide_registro_salud)

    def test_el_cv_reconoce_los_oficios_nuevos(self):
        from accounts.cv import proponer_perfil
        relleno = '\nExperiencia\nTrabajos para clientes particulares 2015-2024\n' + 'texto de relleno ' * 10
        casos = {'Abogada': 'asesoria-legal', 'Editor de video': 'edicion-de-video',
                 'Community manager': 'marketing-y-rrpp', 'Mecánico automotriz': 'mecanica-automotriz'}
        for oficio, slug in casos.items():
            datos = proponer_perfil(f'Camila Rojas Soto\n{oficio}\n+56 9 8765 4321' + relleno)
            self.assertEqual(datos.get('category'), self.cat[slug].pk, oficio)
        datos = proponer_perfil('Camila Rojas Soto\nArquitecto de software\n+56 9 8765 4321' + relleno)
        self.assertNotEqual(datos.get('category'), self.cat['arquitectura'].pk,
                            'un arquitecto de software no es de Arquitectura y planos')
