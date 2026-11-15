"""Mejoras de Pedro (15-11-2026): cobertura, rubros de belleza y varios estudios.

Pedro, con quien nació la idea de ServiPlace, mandó cuatro audios:
1. "La página te pide una sola comuna, entonces cuando la gente busque por otras
   comunas no aparece tu servicio": quien atiende toda la RM solo salía en su
   comuna. Se protege que aparezca en las comunas que marca (o en toda su
   región), sin repetirse, que los de la comuna vayan primero, que una página
   que solo tiene perfiles de cobertura quede fuera del índice, y lo que ve el
   cliente en la tarjeta, la ficha y el schema.
2. En belleza "solo había peluquería" y faltaba uno general.
3. "Hay gente que estudió en más de un lugar" y el campo era una línea; y darle
   más énfasis a completar el perfil.
"""
import time
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory import seo
from directory.busqueda import rubros_de_la_busqueda
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class Base(TestCase):

    def setUp(self):
        self.rm = Region.objects.create(name='Región Metropolitana de Santiago', slug='region-metropolitana-de-santiago')
        self.valpo = Region.objects.create(name='Región de Valparaíso', slug='region-de-valparaiso')
        c = lambda nombre, slug, region: Commune.objects.create(region=region, name=nombre, slug=slug)
        self.maipu = c('Maipú', 'maipu', self.rm)
        self.cerrillos = c('Cerrillos', 'cerrillos', self.rm)
        self.las_condes = c('Las Condes', 'las-condes', self.rm)
        self.santiago = c('Santiago', 'santiago', self.rm)
        self.vina = c('Viña del Mar', 'vina-del-mar', self.valpo)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = {x.slug: x for x in Category.objects.all()}
        self.user = User.objects.create_user('pedro', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def _datos(self, **extra):
        datos = {
            'business_name': 'Gasfitería Pérez', 'contact_name': 'Juan Pérez', 'category': self.cat['gasfiteria'].pk,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': 'Gásfiter en Maipú y alrededores.',
            'description': 'Destapes, calefont y filtraciones.', 'phone': '+56 9 8765 4321',
            'whatsapp_number': '+56 9 8765 4321', 'attends_home': 'on',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return datos

    def publicar(self, **extra):
        r = self.client.post(reverse('accounts:provider_create'), self._datos(**extra))
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        return Provider.objects.filter(owner=self.user).order_by('-pk').first()

    def otro(self, nombre, comuna, **campos):
        """Un perfil público de otro dueño, creado directo (sin formulario)."""
        dueno = User.objects.create_user(nombre.lower().replace(' ', ''), password='clave-larga-de-verdad-99')
        return Provider.objects.create(
            business_name=nombre, contact_name=nombre, owner=dueno, category=self.cat['gasfiteria'], commune=comuna,
            sector='Centro', description='x', short_description='x', phone='+56 9 1111 2222',
            whatsapp_number='56911112222', is_active=True, **campos)

    def listado(self, comuna, rubro='gasfiteria'):
        return self.client.get(reverse('directory:listado_rubro_comuna', kwargs={'rubro': rubro, 'comuna': comuna.slug}))


class Cobertura(Base):

    def test_aparece_en_las_comunas_que_marca(self):
        self.publicar(comunas_atendidas=[self.cerrillos.pk, self.las_condes.pk])
        for comuna in (self.cerrillos, self.las_condes, self.maipu):
            r = self.listado(comuna)
            self.assertEqual(r.status_code, 200, comuna)
            self.assertContains(r, 'Gasfitería Pérez')
        r = self.client.get(reverse('directory:listado_comuna', kwargs={'comuna': 'cerrillos'}))
        self.assertContains(r, 'Gasfitería Pérez')

    def test_sin_cobertura_solo_aparece_en_su_comuna(self):
        """El caso de siempre no cambia: sin marcar nada, Cerrillos sigue vacío (404)."""
        self.publicar()
        self.assertEqual(self.listado(self.cerrillos).status_code, 404)
        self.assertEqual(self.listado(self.maipu).status_code, 200)

    def test_la_comuna_base_no_se_guarda_como_cobertura(self):
        p = self.publicar(comunas_atendidas=[self.maipu.pk, self.cerrillos.pk])
        self.assertEqual(list(p.comunas_atendidas.all()), [self.cerrillos])

    def test_toda_la_region_aparece_en_su_region_y_no_en_otra(self):
        self.publicar(atiende_toda_la_region='on')
        for comuna in (self.cerrillos, self.las_condes, self.santiago):
            self.assertContains(self.listado(comuna), 'Gasfitería Pérez')
        self.assertEqual(self.listado(self.vina).status_code, 404, 'toda la RM no incluye Valparaíso')

    def test_no_se_repite_con_cobertura_rubros_y_region(self):
        """Marcar la comuna, tener otro rubro y toda la región a la vez: sale una vez."""
        p = self.publicar(atiende_toda_la_region='on', comunas_atendidas=[self.cerrillos.pk],
                          otras_categorias=[self.cat['electricidad'].pk])
        r = self.client.get(reverse('directory:listado_comuna', kwargs={'comuna': 'cerrillos'}))
        self.assertEqual(r.context['total_resultados'], 1)
        self.assertEqual(list(Provider.objects.publicos().que_atienden(self.cerrillos)), [p])

    def test_los_de_la_comuna_van_primero(self):
        self.otro('Zeta Local', self.cerrillos)
        cobertura = self.otro('Alfa Cobertura', self.maipu)
        cobertura.comunas_atendidas.add(self.cerrillos)
        nombres = [p.business_name for p in self.listado(self.cerrillos).context['providers']]
        self.assertEqual(nombres, ['Zeta Local', 'Alfa Cobertura'], 'el de la comuna antes, aunque el alfabeto diga otra cosa')

    def test_una_comuna_solo_con_cobertura_queda_fuera_del_indice(self):
        self.publicar(comunas_atendidas=[self.cerrillos.pk])
        r = self.listado(self.cerrillos)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['robots'], 'noindex, follow')
        self.assertEqual(self.listado(self.maipu).context['robots'], '', 'su comuna base sí se indexa')
        self.otro('Local Cerrillos', self.cerrillos)
        self.assertEqual(self.listado(self.cerrillos).context['robots'], '', 'con uno de la comuna, se indexa')

    def test_la_tarjeta_dice_que_atiende_y_desde_donde(self):
        self.publicar(comunas_atendidas=[self.cerrillos.pk])
        r = self.listado(self.cerrillos)
        self.assertContains(r, 'Atiende en Cerrillos')
        self.assertContains(r, 'Desde Maipú')
        self.assertNotContains(self.listado(self.maipu), 'Atiende en')

    def test_los_rubros_de_la_comuna_cuentan_la_cobertura(self):
        self.publicar(comunas_atendidas=[self.cerrillos.pk])
        r = self.client.get(reverse('directory:listado_comuna', kwargs={'comuna': 'cerrillos'}))
        self.assertIn('gasfiteria', [f['category__slug'] for f in r.context['relacionados_categorias']])

    def test_la_ficha_y_el_schema_muestran_la_cobertura(self):
        p = self.publicar(comunas_atendidas=[self.las_condes.pk, self.cerrillos.pk])
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, 'Maipú, Cerrillos y Las Condes')
        self.assertEqual([z['name'] for z in seo._zona(p)], ['Maipú', 'Cerrillos', 'Las Condes'])
        p.atiende_toda_la_region = True
        p.save()
        self.assertContains(self.client.get(p.get_absolute_url()), 'Toda la Región Metropolitana de Santiago')
        self.assertEqual(seo._zona(Provider.objects.get(pk=p.pk)),
                         {'@type': 'AdministrativeArea', 'name': 'Región Metropolitana de Santiago'})

    def test_sin_cobertura_la_ficha_usa_el_texto_libre(self):
        p = self.publicar(service_area='Envíos a todo Chile')
        self.assertContains(self.client.get(p.get_absolute_url()), 'Envíos a todo Chile')
        self.assertEqual(seo._zona(p), 'Envíos a todo Chile')

    def test_editar_agrega_y_quita_comunas(self):
        p = self.publicar()
        url = reverse('accounts:provider_edit', args=[p.slug])
        self.client.post(url, self._datos(comunas_atendidas=[self.cerrillos.pk, self.santiago.pk]))
        self.assertEqual(sorted(c.slug for c in p.comunas_atendidas.all()), ['cerrillos', 'santiago'])
        self.client.post(url, self._datos())
        self.assertEqual(p.comunas_atendidas.count(), 0, 'desmarcar todo las saca')

    def test_tope_de_comunas(self):
        with mock.patch.object(Provider, 'MAX_COMUNAS_ATENDIDAS', 1):
            r = self.client.post(reverse('accounts:provider_create'),
                                 self._datos(comunas_atendidas=[self.cerrillos.pk, self.las_condes.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertIn('toda la región', str(r.context['form'].errors['comunas_atendidas']))
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())

    def test_el_formulario_abre_la_region_de_la_base_y_trae_los_sectores(self):
        r = self.client.get(reverse('accounts:provider_create'))
        self.assertContains(r, 'name="atiende_toda_la_region"')
        self.assertContains(r, 'data-sector="Oriente"')
        info = r.context['form'].cobertura_info()
        self.assertEqual(info['rm'], self.rm.pk)
        self.assertIn(self.las_condes.pk, info['sectores']['Oriente'])
        p = self.publicar(comunas_atendidas=[self.cerrillos.pk])
        form = self.client.get(reverse('accounts:provider_edit', args=[p.slug])).context['form']
        region, comunas, abierta = form.comunas_por_region()[0]
        self.assertEqual(region, self.rm)
        self.assertTrue(abierta)
        self.assertIn((self.cerrillos.pk, 'Cerrillos', True), comunas)


class OtrosEstudios(Base):

    def test_se_guardan_limpios_y_se_muestran_en_la_ficha(self):
        p = self.publicar(profession_title='Kinesiólogo', institution='Universidad Mayor',
                          otros_estudios='Magíster en Deporte, Universidad de Chile, 2023\n\n- Diplomado en punción seca, 2024\n')
        self.assertEqual(p.otros_estudios, 'Magíster en Deporte, Universidad de Chile, 2023\nDiplomado en punción seca, 2024')
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, 'Otros estudios')
        self.assertContains(r, '<li>Diplomado en punción seca, 2024</li>', html=True)

    def test_solo_otros_estudios_ya_muestra_la_formacion(self):
        p = self.publicar(otros_estudios='Curso de instalador SEC, INACAP, 2022')
        self.assertTrue(p.has_professional_info)
        self.assertContains(self.client.get(p.get_absolute_url()), 'Curso de instalador SEC')

    def test_la_busqueda_encuentra_por_otros_estudios(self):
        self.publicar(otros_estudios='Diplomado en climatización industrial, 2021')
        r = self.client.get(reverse('directory:provider_list'), {'q': 'climatización industrial'})
        self.assertContains(r, 'Gasfitería Pérez')

    def test_topes_de_lineas_y_largo(self):
        siete = '\n'.join(f'Curso {n}' for n in range(7))
        r = self.client.post(reverse('accounts:provider_create'), self._datos(otros_estudios=siete))
        self.assertIn('Hasta 6', str(r.context['form'].errors['otros_estudios']))
        r = self.client.post(reverse('accounts:provider_create'), self._datos(otros_estudios='x' * 161))
        self.assertIn('160', str(r.context['form'].errors['otros_estudios']))
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())


class Completitud(Base):

    def test_dice_cuanto_falta_y_que(self):
        p = self.publicar()
        c = p.completitud()
        self.assertLess(c['porcentaje'], 100)
        textos = [f['texto'] for f in c['faltan']]
        self.assertIn('Marca en qué comunas atiendes', textos)
        self.assertIn('Agrega tu formación o tus cursos', textos)
        p.comunas_atendidas.add(self.cerrillos)
        self.assertNotIn('Marca en qué comunas atiendes', [f['texto'] for f in p.completitud()['faltan']])

    def test_a_una_tienda_no_se_le_pide_formacion(self):
        p = self.publicar(category=self.cat['maquillaje-y-cosmetica'].pk)
        self.assertNotIn('Agrega tu formación o tus cursos', [f['texto'] for f in p.completitud()['faltan']])

    def test_a_una_empresa_cargada_desde_su_sitio_tampoco(self):
        """Visto en producción el 15-11: el panel le pedía formación a Max Services SpA."""
        p = self.otro('Max Services SpA', self.maipu, source_name='cliente-gogodevs')
        self.assertNotIn('Agrega tu formación o tus cursos', [f['texto'] for f in p.completitud()['faltan']])
        self.assertIn('Agrega tu formación o tus cursos',
                      [f['texto'] for f in self.otro('Kine Independiente', self.maipu).completitud()['faltan']])

    def test_el_panel_lo_muestra_con_enlace_a_esa_parte_del_formulario(self):
        p = self.publicar()
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(r, f'Tu perfil está al {p.completitud()["porcentaje"]}%')
        self.assertContains(r, reverse('accounts:provider_edit', args=[p.slug]) + '#cobertura')


class RubrosDeBelleza(Base):

    def test_existen_en_belleza_y_el_seed_no_duplica(self):
        for slug in ('belleza-integral', 'maquillaje-profesional', 'masajes-y-spa'):
            self.assertEqual(self.cat[slug].group, Category.BELLEZA, slug)
        antes = Category.objects.count()
        call_command('seed_categorias', stdout=StringIO())
        self.assertEqual(Category.objects.count(), antes)

    def test_la_busqueda_los_entiende(self):
        self.assertIn(self.cat['masajes-y-spa'].pk, rubros_de_la_busqueda('masajista'))
        self.assertIn(self.cat['maquillaje-profesional'].pk, rubros_de_la_busqueda('maquilladora'))
        self.assertIn(self.cat['belleza-integral'].pk, rubros_de_la_busqueda('salón de belleza'))
