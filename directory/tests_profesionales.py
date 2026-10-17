"""ServiPlace para profesionales independientes (17-10-2026).

El directorio deja de ser solo de oficios del hogar: kinesiólogos,
psicólogos, profes particulares y otros independientes publican su perfil,
sobre todo los recién titulados, que no necesitan un empleador sino clientes.

Lo que se protege acá, en orden de gravedad:
  1. Nadie ofrece atención de salud sin estar titulado (ejercicio ilegal).
  2. El perfil profesional se guarda y se ve de punta a punta.
  3. Los formularios públicos dejan de tratar a la gente real como spam y
     "Reclamar perfil" vuelve a funcionar (los dos estaban rotos en vivo).
  4. El catálogo agrupado no multiplica consultas.
"""
import re
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, ProviderReport, Region

User = get_user_model()
ANIO = timezone.localdate().year


def sello_humano(segundos=60):
    """Un sello firmado como lo emite el formulario, de hace `segundos`."""
    return signing.dumps(int(time.time()) - segundos, salt='antispam')


class Base(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='Biobío', slug='biobio', is_active=True)
        self.comuna = Commune.objects.create(region=self.region, name='Concepción',
                                             slug='concepcion', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.kine = Category.objects.get(slug='kinesiologia')
        self.clases = Category.objects.get(slug='clases-particulares')
        self.gasfiter = Category.objects.get(slug='gasfiteria')

    def _perfil(self, categoria, nombre='Perfil', **extra):
        datos = dict(
            business_name=nombre, contact_name='Camila', category=categoria, commune=self.comuna,
            sector='Centro', description='Descripción.', short_description='Corta.',
            phone='+56 9 1111 2222', whatsapp_number='56911112222', is_active=True,
        )
        datos.update(extra)
        return Provider.objects.create(**datos)

    def _datos_formulario(self, categoria, **extra):
        datos = {
            'business_name': 'Camila Rojas Kinesiología', 'contact_name': 'Camila Rojas',
            'category': categoria.pk, 'commune': self.comuna.pk, 'sector': 'Lomas de San Andrés',
            'short_description': 'Kinesióloga a domicilio, rehabilitación y adulto mayor.',
            'description': 'Atiendo a domicilio en Concepción y Talcahuano.',
            'phone': '+56 9 8765 4321', 'whatsapp_number': '+56 9 8765 4321',
            'email': '', 'address': '', 'service_area': 'Concepción y Talcahuano',
            'attends_home': 'on', 'attends_online': 'on',
            'profession_title': 'Kinesióloga', 'institution': 'Universidad de Concepción',
            'graduation_year': str(ANIO - 1), 'health_registry': '654321',
            TIMESTAMP_FIELD: sello_humano(), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return datos


# ─────────────────────────────────────────────────────────────────────────
# Catálogo
# ─────────────────────────────────────────────────────────────────────────
class CatalogoDeCategorias(Base):

    def test_suma_las_profesiones_y_deja_los_oficios_en_hogar(self):
        self.assertEqual(Category.objects.count(), 27)
        self.assertEqual(Category.objects.filter(group=Category.HOGAR).count(), 9)
        self.assertTrue(self.kine.pide_registro_salud)
        self.assertFalse(self.clases.pide_registro_salud)

    def test_correr_el_seed_otra_vez_no_crea_ni_pisa_nada(self):
        """Corre en cada build: si pisara, cada deploy desharía lo editado en el admin."""
        self.kine.name = 'Kinesiología (editada)'
        self.kine.save()
        salida = StringIO()
        call_command('seed_categorias', stdout=salida)
        self.assertIn('0 creadas', salida.getvalue())
        self.assertEqual(Category.objects.get(slug='kinesiologia').name, 'Kinesiología (editada)')

    def test_la_base_de_produccion_queda_con_las_27_y_los_oficios_en_hogar(self):
        """El orden real de build.sh sobre una base vacía: fixture y después seed."""
        Provider.objects.all().delete()
        Category.objects.all().delete()
        Commune.objects.all().delete()
        Region.objects.all().delete()
        call_command('cargar_directorio_inicial', stdout=StringIO())
        call_command('seed_categorias', stdout=StringIO())
        self.assertEqual(Category.objects.count(), 27)
        self.assertEqual(Category.objects.get(slug='gasfiteria').group, Category.HOGAR)
        self.assertEqual(Provider.objects.count(), 361)


# ─────────────────────────────────────────────────────────────────────────
# Portada y landing
# ─────────────────────────────────────────────────────────────────────────
class PortadaYLanding(Base):

    def test_la_portada_muestra_los_grupos_y_anima_a_publicar_donde_no_hay_nadie(self):
        self._perfil(self.gasfiter)
        html = self.client.get(reverse('core:home')).content.decode()
        for grupo in ('Hogar y oficios', 'Salud y bienestar', 'Clases y educación'):
            self.assertIn(grupo, html)
        self.assertIn('1 perfil', html)
        self.assertIn('Sé el primero en publicar', html)
        self.assertIn(reverse('core:para_profesionales'), html)

    def test_la_portada_no_hace_una_consulta_por_categoria(self):
        """G-04: 27 categorías no pueden ser 27 consultas."""
        self.client.get(reverse('core:home'))
        with self.assertNumQueries(8) as con_27:
            self.client.get(reverse('core:home'))
        for i in range(10):
            Category.objects.create(name=f'Extra {i}', slug=f'extra-{i}', group=Category.PROFESIONAL)
        with self.assertNumQueries(len(con_27.captured_queries)):
            self.client.get(reverse('core:home'))

    def test_los_pines_del_mapa_son_comunas_reales_con_su_cifra(self):
        """El mapa es ilustrativo; las cifras no pueden serlo."""
        for i in range(3):
            self._perfil(self.gasfiter, f'Gásfiter {i}')
        html = self.client.get(reverse('core:home')).content.decode()
        self.assertIn('?comuna=concepcion"><i>3</i>Concepción', html)
        self.assertIn('Mapa ilustrativo', html)

    def test_publicar_esta_a_la_vista_sin_competir_con_buscar(self):
        html = self.client.get(reverse('core:home')).content.decode()
        self.assertIn('Quiero publicar mis servicios', html)
        self.assertIn('name="comuna"', html, 'el buscador de la portada pide la comuna')

    def test_la_landing_de_profesionales_responde_y_lleva_al_registro(self):
        r = self.client.get(reverse('core:para_profesionales'))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn(reverse('accounts:register'), html)
        self.assertIn('bolsa de trabajo', html)
        self.assertIn('Kinesiología', html)
        self.assertNotIn('Gasfitería', html, 'la landing es para profesionales, no para oficios')

    def test_la_landing_esta_en_el_sitemap(self):
        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/profesionales/', xml)


# ─────────────────────────────────────────────────────────────────────────
# Listado
# ─────────────────────────────────────────────────────────────────────────
class ListadoPorGrupo(Base):

    def test_filtra_por_grupo(self):
        self._perfil(self.kine, 'Kine Uno')
        self._perfil(self.gasfiter, 'Gásfiter Uno')
        html = self.client.get(reverse('directory:provider_list') + '?grupo=salud').content.decode()
        self.assertIn('Kine Uno', html)
        self.assertNotIn('Gásfiter Uno', html)
        self.assertIn('Salud y bienestar en Chile', html)

    def test_un_grupo_inventado_se_ignora(self):
        self._perfil(self.gasfiter, 'Gásfiter Uno')
        r = self.client.get(reverse('directory:provider_list') + '?grupo=<script>')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Gásfiter Uno', r.content.decode())

    def test_se_encuentra_por_la_profesion(self):
        self._perfil(self.kine, 'Camila R.', profession_title='Kinesióloga deportiva')
        self._perfil(self.gasfiter, 'Gásfiter Uno')
        html = self.client.get(reverse('directory:provider_list') + '?q=deportiva').content.decode()
        self.assertIn('Camila R.', html)
        self.assertNotIn('Gásfiter Uno', html)

    def test_el_contador_dice_el_total_y_no_los_de_la_pagina(self):
        """Decía "24 resultados" con 361: contaba la página, no la búsqueda."""
        for i in range(30):
            self._perfil(self.gasfiter, f'Gásfiter {i:02d}')
        html = self.client.get(reverse('directory:provider_list')).content.decode()
        self.assertIn('<strong>30</strong> resultados', html)

    def test_una_especialidad_vacia_invita_a_publicar(self):
        html = self.client.get(reverse('directory:provider_list') + '?categoria=kinesiologia').content.decode()
        self.assertIn('Todavía no hay perfiles de Kinesiología', html)
        self.assertIn(reverse('accounts:register'), html)


# ─────────────────────────────────────────────────────────────────────────
# Ficha
# ─────────────────────────────────────────────────────────────────────────
class FichaProfesional(Base):

    def test_muestra_la_formacion_y_el_registro_comprobable(self):
        p = self._perfil(self.kine, 'Camila R.', profession_title='Kinesióloga',
                         institution='Universidad de Concepción', graduation_year=ANIO - 1,
                         health_registry='654321', attends_home=True, attends_online=True)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('Formación', html)
        self.assertIn('Universidad de Concepción', html)
        self.assertIn(f'titulado/a en {ANIO - 1}', html)
        self.assertIn('N° 654321', html)
        self.assertIn('rnpi.superdesalud.gob.cl', html)
        self.assertIn('A domicilio', html)
        self.assertIn('Online', html)

    def test_un_gasfiter_sin_formacion_no_muestra_el_bloque(self):
        """Un oficio no tiene por qué tener título: no puede verse incompleto."""
        p = self._perfil(self.gasfiter, 'Gásfiter Uno')
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertNotIn('Formación', html)
        self.assertNotIn('rnpi.superdesalud.gob.cl', html)

    def test_quien_aun_estudia_se_ve_como_estudiante(self):
        p = self._perfil(self.clases, 'Profe Pedro', profession_title='Estudiante de Pedagogía',
                         graduation_year=ANIO + 1)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn(f'se titula en {ANIO + 1}', html)
        self.assertNotIn(f'titulado/a en {ANIO + 1}', html)

    def test_el_mensaje_de_whatsapp_no_pide_cotizacion(self):
        """A un psicólogo no se le pide "cotización"."""
        p = self._perfil(self.kine)
        r = self.client.get(reverse('directory:whatsapp_redirect', args=[p.slug]))
        self.assertNotIn('cotizaci', r['Location'].lower())


# ─────────────────────────────────────────────────────────────────────────
# Publicar
# ─────────────────────────────────────────────────────────────────────────
class PublicarPerfilProfesional(Base):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('camila', email='c@example.cl', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def test_se_guarda_de_punta_a_punta(self):
        """Comprueba que el perfil EXISTE: una prueba que solo mira "si existe,
        que esté bien" pasa igual cuando el formulario no guarda nada."""
        r = self.client.post(reverse('accounts:provider_create'), self._datos_formulario(self.kine))
        p = Provider.objects.filter(owner=self.user).first()
        self.assertIsNotNone(p, f'no se guardó; errores: {r.context["form"].errors if r.context else ""}')
        self.assertEqual(p.profession_title, 'Kinesióloga')
        self.assertEqual(p.graduation_year, ANIO - 1)
        self.assertEqual(p.health_registry, '654321')
        self.assertTrue(p.attends_home and p.attends_online)
        self.assertFalse(p.attends_office)
        self.assertTrue(p.is_active)

    def test_no_se_ofrece_salud_sin_estar_titulado(self):
        """Ejercicio ilegal de la profesión: quien está en práctica no publica como kinesiólogo."""
        r = self.client.post(reverse('accounts:provider_create'),
                             self._datos_formulario(self.kine, graduation_year=str(ANIO + 1)))
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())
        self.assertIn('solo puede ofrecerla quien ya está titulado', r.content.decode())

    def test_quien_estudia_si_puede_publicar_clases(self):
        self.client.post(reverse('accounts:provider_create'),
                         self._datos_formulario(self.clases, graduation_year=str(ANIO + 1), health_registry=''))
        self.assertTrue(Provider.objects.filter(owner=self.user, category=self.clases).exists())

    def test_el_registro_de_salud_es_solo_numeros(self):
        r = self.client.post(reverse('accounts:provider_create'),
                             self._datos_formulario(self.kine, health_registry='abc123'))
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())
        self.assertIn('solo números', r.content.decode())

    def test_un_anio_absurdo_se_rechaza(self):
        r = self.client.post(reverse('accounts:provider_create'),
                             self._datos_formulario(self.clases, graduation_year='1800', health_registry=''))
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())
        self.assertIn('Escribe un año entre', r.content.decode())

    def test_lo_que_escribe_en_titulo_e_institucion_no_se_ejecuta(self):
        self.client.post(reverse('accounts:provider_create'), self._datos_formulario(
            self.kine, profession_title='<script>alert(1)</script>Kinesióloga',
            institution='<img src=x onerror=alert(1)>UdeC'))
        p = Provider.objects.get(owner=self.user)
        self.assertNotIn('<', p.profession_title + p.institution)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertNotIn('<img src=x', html)

    def test_el_formulario_muestra_el_error_de_cada_campo(self):
        """Antes solo el nombre mostraba su error: un WhatsApp mal escrito
        devolvía el formulario sin decir por qué."""
        r = self.client.post(reverse('accounts:provider_create'),
                             self._datos_formulario(self.kine, whatsapp_number='123'))
        self.assertIn('El WhatsApp debe ser un celular chileno', r.content.decode())

    def test_el_rubro_viene_agrupado(self):
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('<optgroup label="Salud y bienestar">', html)


# ─────────────────────────────────────────────────────────────────────────
# Antispam: la gente real dejaba de verse como spam
# ─────────────────────────────────────────────────────────────────────────
class AntispamEnLosFormularios(Base):

    def _sello_de(self, html):
        m = re.search(rf'name="{TIMESTAMP_FIELD}" value="([^"]+)"', html)
        return m.group(1) if m else None

    def test_el_formulario_de_publicar_dibuja_el_sello(self):
        """Sin el sello, toda persona sumaba 20 puntos ("sin_sello")."""
        user = User.objects.create_user('x', password='clave-larga-de-verdad-99')
        self.client.force_login(user)
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        sello = self._sello_de(html)
        self.assertIsNotNone(sello, 'el formulario no dibuja el sello del antispam')
        signing.loads(sello, salt='antispam')  # firma válida: no lanza

    def test_el_registro_esconde_el_honeypot(self):
        html = self.client.get(reverse('accounts:register')).content.decode()
        self.assertIsNotNone(self._sello_de(html))
        self.assertNotIn('Deja este campo vacío', html, 'el honeypot se ve con su etiqueta')
        self.assertNotIn('Sello formulario', html)
        self.assertRegex(html, rf'class="hp-wrap"[^>]*>.*name="{HONEYPOT_FIELD}"')

    def test_un_profesional_con_dos_enlaces_no_queda_oculto(self):
        """Instagram + web en la descripción eran 20 puntos; con "sin_sello",
        40: el perfil quedaba oculto como spam."""
        user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(user)
        self.client.post(reverse('accounts:provider_create'), self._datos_formulario(
            self.kine, description='Mi Instagram: https://instagram.com/camila y mi web https://camila.cl'))
        p = Provider.objects.get(owner=user)
        self.assertFalse(p.spam_flag, p.spam_reasons)
        self.assertTrue(p.is_active)


# ─────────────────────────────────────────────────────────────────────────
# Reclamar perfil: estaba roto en vivo
# ─────────────────────────────────────────────────────────────────────────
class ReclamarPerfil(Base):

    def setUp(self):
        super().setUp()
        self.perfil = self._perfil(self.gasfiter, 'Gásfiter de Google Maps', source_name='Google Maps')
        self.user = User.objects.create_user('dueno', email='d@example.cl', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)
        self.url = reverse('accounts:claim_profile', args=[self.perfil.slug])

    def test_el_formulario_trae_los_campos_que_exige(self):
        html = self.client.get(self.url).content.decode()
        for campo in ('reporter_name', 'reporter_contact', 'message', 'kind', TIMESTAMP_FIELD):
            self.assertIn(f'name="{campo}"', html, f'falta {campo}: el reclamo sale inválido en silencio')

    def test_enviar_lo_que_dibuja_el_formulario_crea_la_solicitud(self):
        html = self.client.get(self.url).content.decode()
        datos = dict(re.findall(r'name="(kind|reporter_name|reporter_contact|' + TIMESTAMP_FIELD + r')"[^>]*value="([^"]*)"', html))
        datos['message'] = re.search(r'name="message"[^>]*>([^<]*)</textarea>', html).group(1)
        datos[HONEYPOT_FIELD] = ''
        r = self.client.post(self.url, datos)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ProviderReport.objects.filter(
            provider=self.perfil, claimant=self.user, kind=ProviderReport.CLAIM).exists())

    def test_una_segunda_visita_avisa_que_ya_esta_pendiente(self):
        ProviderReport.objects.create(provider=self.perfil, claimant=self.user, kind=ProviderReport.CLAIM,
                                      reporter_name='Dueño', reporter_contact='d@example.cl',
                                      message='Es mío, confírmenlo por WhatsApp.')
        html = self.client.get(self.url).content.decode()
        self.assertIn('Ya enviaste una solicitud', html)


# ─────────────────────────────────────────────────────────────────────────
# Registro: redirección abierta
# ─────────────────────────────────────────────────────────────────────────
class RegistroNoRedirigeAOtroSitio(TestCase):

    def _registrar(self, next_url):
        return self.client.post(reverse('accounts:register') + f'?next={next_url}', {
            'username': 'nuevo', 'email': 'n@example.cl',
            'password1': 'clave-larga-de-verdad-99', 'password2': 'clave-larga-de-verdad-99',
            TIMESTAMP_FIELD: sello_humano(), HONEYPOT_FIELD: '',
        })

    def test_una_url_que_empieza_con_doble_barra_no_sale_del_sitio(self):
        r = self._registrar('//sitio-ajeno.example/login')
        self.assertEqual(r.status_code, 302)
        self.assertNotIn('sitio-ajeno', r['Location'])

    def test_un_next_interno_se_respeta(self):
        r = self._registrar('/servicios/')
        self.assertEqual(r['Location'], '/servicios/')


# ─────────────────────────────────────────────────────────────────────────
# Panel de cuenta: daba 500 a todo usuario con sesión
# ─────────────────────────────────────────────────────────────────────────
class PanelDeCuenta(Base):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def test_el_panel_responde(self):
        """Es adonde lleva el login. Usaba ProviderReport.CLAIM, que no existía."""
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)

    def test_muestra_las_visitas_y_clics_de_verdad(self):
        """Mostraba "—" fijo aunque la vista los calculaba."""
        self._perfil(self.kine, 'Camila R.', owner=self.user, views_count=37, whatsapp_clicks_count=5)
        html = self.client.get(reverse('accounts:dashboard')).content.decode()
        self.assertIn('<strong>37</strong>', html)
        self.assertIn('<strong>5</strong>', html)

    def test_no_dice_verificado_si_no_lo_esta(self):
        """Decía "activo" en "estado verificado" con solo tener un perfil."""
        self._perfil(self.kine, 'Camila R.', owner=self.user, is_verified=False)
        html = self.client.get(reverse('accounts:dashboard')).content.decode()
        self.assertNotIn('perfil verificado', html)
        self.assertIn('cómo obtenerlo', html)


class AprobarReclamoEnElAdmin(Base):
    """El reclamo no asigna solo: se aprueba en el admin, en un clic."""

    def test_aprobar_pasa_el_perfil_a_quien_lo_reclamo(self):
        from django.contrib.admin.sites import site
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        perfil = self._perfil(self.gasfiter, 'Gásfiter de Maps', source_name='Google Maps')
        dueno = User.objects.create_user('dueno', password='clave-larga-de-verdad-99')
        reporte = ProviderReport.objects.create(provider=perfil, claimant=dueno, kind=ProviderReport.CLAIM,
                                                reporter_name='Dueño', reporter_contact='+56 9 1111 2222',
                                                message='Es mío, confírmenlo por WhatsApp.')
        admin_user = User.objects.create_superuser('admin', 'a@b.cl', 'x')
        request = RequestFactory().post('/')
        request.user = admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        modelo_admin = site._registry[ProviderReport]
        modelo_admin.aprobar_reclamo(request, ProviderReport.objects.filter(pk=reporte.pk))
        perfil.refresh_from_db()
        reporte.refresh_from_db()
        self.assertEqual(perfil.owner, dueno)
        self.assertEqual(perfil.data_status, Provider.AUTHORIZED)
        self.assertIsNotNone(reporte.resolved_at)

    def test_no_le_quita_el_perfil_a_quien_ya_es_dueno(self):
        from django.contrib.admin.sites import site
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        dueno_real = User.objects.create_user('real', password='clave-larga-de-verdad-99')
        perfil = self._perfil(self.gasfiter, 'Gásfiter con dueño', owner=dueno_real)
        intruso = User.objects.create_user('intruso', password='clave-larga-de-verdad-99')
        reporte = ProviderReport.objects.create(provider=perfil, claimant=intruso, kind=ProviderReport.CLAIM,
                                                reporter_name='X', reporter_contact='x', message='Es mío, de verdad.')
        request = RequestFactory().post('/')
        request.user = User.objects.create_superuser('admin', 'a@b.cl', 'x')
        request.session = {}
        request._messages = FallbackStorage(request)
        site._registry[ProviderReport].aprobar_reclamo(request, ProviderReport.objects.filter(pk=reporte.pk))
        perfil.refresh_from_db()
        self.assertEqual(perfil.owner, dueno_real)
