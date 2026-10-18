"""Varios rubros por perfil (18-10-2026).

Diego registraba a su suegro (construcción, gasfitería, electricidad y
soldadura) y el formulario lo obligaba a elegir uno. Lo que se protege: que el
perfil aparezca en el listado de cada uno de sus rubros SIN repetirse, que los
conteos, el sitemap y los enlaces lo sepan (un listado que se enlaza vacío es
404), el tope, y que la regla de salud valga también para un rubro extra.
"""
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.cv import proponer_perfil
from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.catalogo import categorias_por_grupo, perfiles_por_rubro
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


class VariosRubros(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = {c.slug: c for c in Category.objects.all()}
        self.user = User.objects.create_user('suegro', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def _datos(self, **extra):
        datos = {
            'business_name': 'Maestro Juan', 'contact_name': 'Juan', 'category': self.cat['construccion'].pk,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': 'Maestro constructor en Maipú.',
            'description': 'Ampliaciones, gasfitería, electricidad y soldadura.', 'phone': '+56 9 8765 4321',
            'whatsapp_number': '+56 9 8765 4321', 'attends_home': 'on',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return datos

    def _otras(self, *slugs):
        return [self.cat[s].pk for s in slugs]

    def _publicar(self, *otras, **extra):
        return self.client.post(reverse('accounts:provider_create'),
                                self._datos(otras_categorias=self._otras(*otras), **extra))

    def _suegro(self):
        self._publicar('gasfiteria', 'electricidad', 'soldadura')
        return Provider.objects.get(owner=self.user)

    def test_se_publica_con_varios_rubros(self):
        p = self._suegro()
        self.assertEqual(p.category.slug, 'construccion')
        self.assertEqual({c.slug for c in p.otras_categorias.all()}, {'gasfiteria', 'electricidad', 'soldadura'})

    def test_aparece_en_el_listado_de_cada_rubro_sin_repetirse(self):
        p = self._suegro()
        for slug in ('construccion', 'gasfiteria', 'electricidad', 'soldadura'):
            for url in (reverse('directory:listado_rubro', args=[slug]),
                        reverse('directory:listado_rubro_comuna', args=[slug, 'maipu'])):
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200, url)
                self.assertContains(r, p.get_absolute_url())
        self.assertEqual(self.client.get(reverse('directory:listado_rubro', args=['pintura'])).status_code, 404)
        # Los cuatro son de Hogar: en el listado del grupo sale UNA vez.
        r = self.client.get(reverse('directory:listado_rubro', args=[Category.GROUP_SLUGS[Category.HOGAR]]))
        self.assertEqual(r.context['total_resultados'], 1)
        self.assertEqual(r.content.decode().count(f'<h3><a href="{p.get_absolute_url()}"'), 1)
        # Y en la búsqueda por texto de un rubro extra, también una vez.
        r = self.client.get(reverse('directory:provider_list'), {'q': 'Soldadura'})
        self.assertEqual(r.context['total_resultados'], 1)

    def test_la_tarjeta_dice_el_rubro_del_listado_y_los_demas(self):
        self._suegro()
        html = self.client.get(reverse('directory:listado_rubro', args=['gasfiteria'])).content.decode()
        self.assertIn('<div class="ficha-top"><b>Gasfitería</b>', html)
        self.assertIn('También: Construcción, Electricidad, Soldadura', html)
        self.assertIn('data-ga-categoria="gasfiteria"', html)

    def test_el_principal_no_se_repite_y_hay_tope(self):
        self._publicar('construccion', 'gasfiteria')
        p = Provider.objects.get(owner=self.user)
        self.assertEqual([c.slug for c in p.otras_categorias.all()], ['gasfiteria'])
        p.delete()
        r = self._publicar('gasfiteria', 'electricidad', 'soldadura', 'pintura', 'carpinteria', 'cerrajeria')
        self.assertContains(r, f'Elige hasta {Provider.MAX_OTROS_RUBROS} rubros además del principal')
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())

    def test_conteos_sitemap_y_guias_cuentan_los_otros_rubros(self):
        self._suegro()
        hogar = next(g for g in categorias_por_grupo() if g['clave'] == Category.HOGAR)
        conteo = {c.slug: c.n_activos for c in hogar['categorias']}
        self.assertEqual((conteo['construccion'], conteo['gasfiteria'], conteo['soldadura'], conteo['pintura']),
                         (1, 1, 1, 0))
        self.assertEqual(perfiles_por_rubro(Provider.objects.publicos())['electricidad'], 1)
        sitemap = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/servicios/soldadura/maipu/', sitemap)
        self.assertEqual(sitemap.count('/servicios/gasfiteria/maipu/'), 1)
        guia = self.client.get(reverse('core:guia', args=['antes-de-contratar-un-maestro'])).content.decode()
        self.assertIn(reverse('directory:listado_rubro', args=['gasfiteria']), guia)

    def test_la_ficha_enlaza_a_sus_otros_rubros(self):
        p = self._suegro()
        html = self.client.get(p.get_absolute_url()).content.decode()
        for slug in ('gasfiteria', 'electricidad', 'soldadura'):
            self.assertIn(reverse('directory:listado_rubro_comuna', args=[slug, 'maipu']), html)
        self.assertIn('"knowsAbout"', html)
        self.assertIn('Gásfiter', html)

    def test_editar_cambia_los_otros_rubros(self):
        p = self._suegro()
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]),
                         self._datos(otras_categorias=self._otras('pintura')))
        self.assertEqual([c.slug for c in p.otras_categorias.all()], ['pintura'])
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]), self._datos())
        self.assertEqual(p.otras_categorias.count(), 0, 'desmarcar todos no los quitó')

    def test_registro_de_salud_si_un_rubro_extra_es_de_salud(self):
        self._publicar('kinesiologia', category=self.cat['clases-particulares'].pk, health_registry='123456')
        self.assertEqual(Provider.objects.get(owner=self.user).health_registry, '123456')
        Provider.objects.filter(owner=self.user).delete()
        self._publicar('gasfiteria', health_registry='123456')
        self.assertEqual(Provider.objects.get(owner=self.user).health_registry, '')

    def test_quien_no_se_titula_no_ofrece_salud_ni_como_rubro_extra(self):
        r = self._publicar('kinesiologia', category=self.cat['clases-particulares'].pk,
                           graduation_year=timezone.localdate().year + 1)
        self.assertContains(r, 'La atención de salud solo puede ofrecerla quien ya está titulado/a')
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())

    def test_el_formulario_muestra_los_otros_rubros(self):
        p = self._suegro()
        html = self.client.get(reverse('accounts:provider_edit', args=[p.slug])).content.decode()
        self.assertIn('¿Haces más de una cosa?', html)
        self.assertIn(f'name="otras_categorias" value="{self.cat["soldadura"].pk}" checked', html)
        self.assertNotIn(f'name="otras_categorias" value="{self.cat["pintura"].pk}" checked', html)

    def test_el_cv_sugiere_los_otros_oficios(self):
        texto = ('Juan Pérez Soto\nMaestro constructor, gásfiter, electricista y soldador\n'
                 'Experiencia\nMaestro constructor en obras menores 2010-2024\nMaipú\n+56 9 8765 4321\n')
        datos = proponer_perfil(texto)
        self.assertEqual(datos.get('category'), self.cat['construccion'].pk)
        self.assertEqual(set(datos.get('otras_categorias', [])), set(self._otras('gasfiteria', 'electricidad', 'soldadura')))

    def test_soldadura_tiene_su_pagina_para_profesionales(self):
        r = self.client.get(reverse('core:profesion', args=['soldadura']))
        self.assertEqual(r.status_code, 200)

    def test_el_listado_no_hace_una_consulta_por_perfil(self):
        """G-04: el 'También:' de cada tarjeta sale del prefetch, no de una consulta por fila."""
        self._suegro()
        url = reverse('directory:listado_rubro', args=['gasfiteria'])
        self.client.get(url)  # la primera visita consume el aviso de "publicado": no se mide
        with CaptureQueriesContext(connection) as uno:
            self.client.get(url)
        for i in range(4):
            otro = Provider.objects.create(
                owner=self.user, business_name=f'Otro {i}', category=self.cat['construccion'], commune=self.maipu,
                short_description='x', whatsapp_number='+56987654321', is_active=True)
            otro.otras_categorias.set([self.cat['gasfiteria'], self.cat['pintura']])
        with CaptureQueriesContext(connection) as cinco:
            self.client.get(url)
        self.assertEqual(len(cinco), len(uno), 'las consultas crecen con la cantidad de perfiles')
