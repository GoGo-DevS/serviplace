"""Páginas de contenido para posicionar (18-10-2026): /profesionales/<rubro>/
y /guias/. Se prueba lo que hace que Google las tome o las descarte:
título y descripción únicos y de largo razonable, un h1, JSON-LD que parsea,
FAQ del schema = FAQ visible, enlaces internos vivos, y nada inventado
(sin precios en las profesiones).
"""
import html
import json
import re
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.guias import GUIAS
from core.profesiones import PROFESIONES
from directory.models import Category, Commune, Provider, Region

User = get_user_model()


def jsonld(html_texto):
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_texto, re.S)]


def titulo(html_texto):
    return html.unescape(re.search(r'<title>(.*?)</title>', html_texto, re.S).group(1).strip())


def meta(html_texto):
    return html.unescape(re.search(r'<meta name="description" content="([^"]*)"', html_texto).group(1))


class Base(TestCase):
    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())


class PaginasDeProfesion(Base):

    def test_cada_especialidad_sembrada_tiene_su_pagina(self):
        """Los chips de /profesionales/ apuntan a estas páginas: una sin
        contenido sería un 404 desde la página de captación."""
        slugs = set(Category.objects.filter(is_active=True).values_list('slug', flat=True))
        self.assertEqual(slugs - set(PROFESIONES), set())
        for slug in slugs:
            self.assertEqual(self.client.get(reverse('core:profesion', args=[slug])).status_code, 200, slug)

    def test_titulos_y_descripciones_unicos_y_de_largo_razonable(self):
        vistos_t, vistos_m = set(), set()
        for slug in PROFESIONES:
            h = self.client.get(reverse('core:profesion', args=[slug])).content.decode()
            t, m = titulo(h), meta(h)
            self.assertLessEqual(len(t), 65, f'{slug}: título de {len(t)} caracteres ({t})')
            self.assertTrue(110 <= len(m) <= 160, f'{slug}: descripción de {len(m)} caracteres')
            self.assertNotIn(t, vistos_t, f'{slug}: título repetido')
            self.assertNotIn(m, vistos_m, f'{slug}: descripción repetida')
            vistos_t.add(t)
            vistos_m.add(m)
            self.assertEqual(h.count('<h1'), 1, slug)

    def test_el_contenido_es_propio_de_cada_especialidad(self):
        """Doorway: si dos páginas comparten la intro o el ejemplo, son la misma
        plantilla con el nombre cambiado."""
        for campo in ('intro', 'ejemplo_corta', 'ejemplo_larga', 'credencial_texto'):
            valores = [c[campo] for c in PROFESIONES.values()]
            self.assertEqual(len(valores), len(set(valores)), f'{campo} repetido entre especialidades')

    def test_sin_precios_ni_signos_de_exclamacion(self):
        for slug, c in PROFESIONES.items():
            texto = json.dumps(c, ensure_ascii=False)
            self.assertNotIn('$', texto, f'{slug}: un precio sin fuente es el error más caro (G-01)')
            self.assertNotIn('¡', texto, slug)

    def test_el_faq_del_schema_es_el_que_se_ve(self):
        h = self.client.get(reverse('core:profesion', args=['kinesiologia'])).content.decode()
        faq = next(b for b in jsonld(h) if b.get('@type') == 'FAQPage')
        # En el <summary> visible, no en cualquier parte: el propio JSON-LD
        # contiene el texto y la prueba pasaría aunque el FAQ no se viera.
        for pregunta in faq['mainEntity']:
            self.assertIn(f"<summary>{html.escape(pregunta['name'], quote=False)}</summary>", h)
        miga = next(b for b in jsonld(h) if b.get('@type') == 'BreadcrumbList')
        self.assertEqual([i['name'] for i in miga['itemListElement']], ['Inicio', 'Para profesionales', 'Kinesiología'])

    def test_salud_enlaza_al_registro_y_oficios_a_la_sec(self):
        kine = self.client.get(reverse('core:profesion', args=['kinesiologia'])).content.decode()
        self.assertIn('rnpi.superdesalud.gob.cl', kine)
        self.assertIn(reverse('core:guia', args=['verificar-registro-profesional-de-salud']), kine)
        gas = self.client.get(reverse('core:profesion', args=['gasfiteria'])).content.decode()
        self.assertIn(reverse('core:guia', args=['verificar-instalador-sec']), gas)
        clases = self.client.get(reverse('core:profesion', args=['clases-particulares'])).content.decode()
        self.assertNotIn('rnpi.superdesalud', clases)

    def test_una_especialidad_inexistente_o_apagada_es_404(self):
        self.assertEqual(self.client.get('/profesionales/astronauta/').status_code, 404)
        Category.objects.filter(slug='pintura').update(is_active=False)
        self.assertEqual(self.client.get('/profesionales/pintura/').status_code, 404)

    def test_muestra_los_perfiles_publicados_solo_si_hay(self):
        url = reverse('core:profesion', args=['gasfiteria'])
        self.assertNotIn('Ver 1 perfil', self.client.get(url).content.decode())
        dueno = User.objects.create_user('d', password='clave-larga-de-verdad-99')
        Provider.objects.create(business_name='Gasfitería Uno', contact_name='Ana',
                                category=Category.objects.get(slug='gasfiteria'), commune=self.maipu, sector='Centro',
                                description='Descripción.', short_description='Resumen.', phone='+56 9 1111 2222',
                                whatsapp_number='56911112222', is_active=True, owner=dueno)
        self.assertIn('Ver 1 perfil de gasfitería', self.client.get(url).content.decode())

    def test_los_chips_de_profesionales_llevan_a_su_pagina(self):
        h = self.client.get(reverse('core:para_profesionales')).content.decode()
        self.assertIn(f'href="{reverse("core:profesion", args=["kinesiologia"])}"', h)


class Guias(Base):

    def test_cada_guia_responde_con_su_articulo(self):
        for g in GUIAS:
            h = self.client.get(reverse('core:guia', args=[g['slug']])).content.decode()
            self.assertEqual(h.count('<h1'), 1, g['slug'])
            self.assertLessEqual(len(titulo(h)), 65, g['slug'])
            self.assertTrue(110 <= len(meta(h)) <= 160, f"{g['slug']}: {len(meta(h))}")
            articulo = next(b for b in jsonld(h) if b.get('@type') == 'Article')
            self.assertEqual(articulo['headline'], g['titulo'])
            self.assertEqual(articulo['dateModified'], g['actualizada'].isoformat())
            self.assertEqual(articulo['author']['name'], 'ServiPlace', 'un autor que es solo @id queda sin nombre')
            self.assertIn('class="guia-fuentes"', h, f"{g['slug']}: sin fuentes citadas")

    def test_los_enlaces_internos_de_las_guias_estan_vivos(self):
        vistos = set()
        for g in GUIAS + [None]:
            url = reverse('core:guias') if g is None else reverse('core:guia', args=[g['slug']])
            h = self.client.get(url).content.decode()
            main = h.split('<main', 1)[1].split('</main>', 1)[0]
            for href in re.findall(r'href="(/[^"#]*)"', main):
                ruta = href.split('?', 1)[0]
                if ruta in vistos:
                    continue
                vistos.add(ruta)
                self.assertEqual(self.client.get(ruta).status_code, 200, f'{url} → {ruta}')

    def test_los_enlaces_externos_abren_aparte_y_sin_opener(self):
        for g in GUIAS:
            h = self.client.get(reverse('core:guia', args=[g['slug']])).content.decode()
            for a in re.findall(r'<a [^>]*href="https?://[^"]+"[^>]*>', h):
                if 'gogodevs.cl' in a:
                    continue
                rel = re.search(r'rel="([^"]*)"', a)
                self.assertTrue(rel and 'noopener' in rel.group(1).split(), f"{g['slug']}: {a}")

    def test_ningun_titulo_salta_un_nivel(self):
        for g in GUIAS:
            h = self.client.get(reverse('core:guia', args=[g['slug']])).content.decode()
            main = h.split('<main', 1)[1].split('</main>', 1)[0]
            niveles = [int(n) for n in re.findall(r'<h([1-6])\b', main)]
            for antes, despues in zip(niveles, niveles[1:]):
                self.assertLessEqual(despues - antes, 1, f"{g['slug']}: h{antes} → h{despues}")

    def test_inexistente_es_404(self):
        self.assertEqual(self.client.get('/guias/no-existe/').status_code, 404)


class Sitemap(Base):

    def test_profesiones_y_guias_estan_en_el_sitemap(self):
        xml = self.client.get('/sitemap.xml').content.decode()
        for slug in PROFESIONES:
            self.assertIn(f'/profesionales/{slug}/</loc>', xml)
        for g in GUIAS:
            self.assertIn(f"/guias/{g['slug']}/</loc>", xml)
        self.assertIn('/guias/</loc>', xml)

    def test_una_especialidad_apagada_sale_del_sitemap(self):
        Category.objects.filter(slug='pintura').update(is_active=False)
        self.assertNotIn('/profesionales/pintura/</loc>', self.client.get('/sitemap.xml').content.decode())


class CredencialesEnElPerfil(Base):
    """La formación va en el schema del perfil como credencial: lo que pesa
    sin reseñas. Solo lo que la ficha muestra, y un estudiante no declara título."""

    def perfil(self, **campos):
        dueno = User.objects.create_user(f'd{Provider.objects.count()}', password='clave-larga-de-verdad-99')
        datos = dict(business_name='Camila Rojas, Kinesióloga', contact_name='Camila Rojas',
                     category=Category.objects.get(slug='kinesiologia'), commune=self.maipu, sector='Centro',
                     description='Descripción.', short_description='Resumen.', phone='+56 9 1111 2222',
                     whatsapp_number='56911112222', is_active=True, owner=dueno)
        datos.update(campos)
        p = Provider.objects.create(**datos)
        h = self.client.get(p.get_absolute_url()).content.decode()
        return next(b for b in jsonld(h) if b.get('@id', '').endswith('#perfil'))

    def test_titulo_institucion_y_registro_como_credenciales(self):
        schema = self.perfil(profession_title='Kinesióloga', institution='Universidad de Concepción',
                             graduation_year=2019, health_registry='654321')
        persona = schema['founder']
        self.assertEqual(persona['name'], 'Camila Rojas')
        self.assertEqual(persona['alumniOf']['name'], 'Universidad de Concepción')
        tipos = {c['credentialCategory']: c for c in persona['hasCredential']}
        self.assertEqual(tipos['degree']['recognizedBy']['name'], 'Universidad de Concepción')
        self.assertIn('654321', tipos['license']['name'])
        self.assertEqual(tipos['license']['recognizedBy']['name'], 'Superintendencia de Salud')

    def test_un_estudiante_no_declara_un_titulo_que_no_tiene(self):
        from django.utils import timezone
        schema = self.perfil(profession_title='Kinesiología', graduation_year=timezone.localdate().year + 1,
                             category=Category.objects.get(slug='clases-particulares'))
        self.assertNotIn('hasCredential', schema['founder'])
