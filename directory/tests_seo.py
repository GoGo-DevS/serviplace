"""SEO técnico (18-10-2026): el checklist de la auditoría de Jorge Urzúa, como pruebas.

Cada prueba corresponde a algo que ya falló en un sitio nuestro (Medina,
Punto Parcelas) o a lo que se vio en ServiPlace: enlaces con "?", una
paginación que generaba "??page=2" y un noindex que nunca se imprimía.
"""
import json
import re
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from directory.models import Category, Commune, Provider, Region

User = get_user_model()


def bloques_jsonld(html):
    """Parsea cada bloque: si uno está mal formado, json.loads revienta y la
    prueba falla, en vez de pasar callada como pasaría buscando el texto."""
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def tipos(bloques):
    salida = set()
    for b in bloques:
        for nodo in b.get('@graph', [b]):
            salida.add(nodo.get('@type'))
    return salida


class Base(TestCase):
    def setUp(self):
        region = Region.objects.create(name='Región Metropolitana de Santiago', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        self.florida = Commune.objects.create(region=region, name='La Florida', slug='la-florida', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.gasfiter = Category.objects.get(slug='gasfiteria')
        self.kine = Category.objects.get(slug='kinesiologia')
        self.dueno = User.objects.create_user('dueno', password='clave-larga-de-verdad-99')

    def _perfil(self, nombre, categoria, comuna, **extra):
        datos = dict(business_name=nombre, contact_name='Ana', category=categoria, commune=comuna, sector='Centro',
                     description='Descripción del servicio.', short_description='Resumen corto.',
                     phone='+56 9 1111 2222', whatsapp_number='56911112222', is_active=True, owner=self.dueno)
        datos.update(extra)
        return Provider.objects.create(**datos)


class URLsLimpias(Base):

    def test_la_pagina_de_mas_valor_tiene_url_limpia_y_h1_con_la_busqueda_real(self):
        self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        url = reverse('directory:listado_rubro_comuna', kwargs={'rubro': 'gasfiteria', 'comuna': 'maipu'})
        self.assertEqual(url, '/servicios/gasfiteria/maipu/')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('<h1 class="h2 mt-2 mb-1">Gásfiter en Maipú</h1>', html)
        self.assertIn('<title>Gásfiter en Maipú | ServiPlace</title>', html)
        self.assertIn(f'<link rel="canonical" href="{settings.SITE_URL}/servicios/gasfiteria/maipu/">', html)

    def test_las_urls_viejas_con_parametros_redirigen_con_301(self):
        r = self.client.get('/servicios/?categoria=gasfiteria&comuna=maipu')
        self.assertEqual((r.status_code, r['Location']), (301, '/servicios/gasfiteria/maipu/'))
        r = self.client.get('/servicios/?comuna=maipu&page=2')
        self.assertEqual((r.status_code, r['Location']), (301, '/servicios/en/maipu/?page=2'))
        r = self.client.get('/servicios/?grupo=salud')
        self.assertEqual(r['Location'], '/servicios/salud-y-bienestar/')

    def test_ningun_enlace_publico_usa_parametros_de_filtro(self):
        """Lo que vio Diego: enlaces con '?categoria=' en la portada y el listado."""
        self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        for url in ('/', '/servicios/', '/servicios/gasfiteria/maipu/', '/profesionales/'):
            html = self.client.get(url).content.decode()
            self.assertNotRegex(html, r'href="[^"]*\?(categoria|comuna|grupo)=', f'enlace con parámetros en {url}')

    def test_la_paginacion_no_genera_doble_signo(self):
        """Generaba href="??page=2": la página 2 nunca cargaba."""
        for i in range(30):
            self._perfil(f'Gasfitería {i:02d}', self.gasfiter, self.maipu)
        html = self.client.get('/servicios/gasfiteria/maipu/').content.decode()
        self.assertNotIn('??', html)
        self.assertIn('href="?page=2"', html)

    def test_un_listado_vacio_es_404_y_noindex(self):
        r = self.client.get('/servicios/kinesiologia/maipu/')
        self.assertEqual(r.status_code, 404)
        self.assertIn('<meta name="robots" content="noindex, follow">', r.content.decode())

    def test_una_especialidad_o_comuna_inventada_es_404(self):
        self.assertEqual(self.client.get('/servicios/no-existe/').status_code, 404)
        self.assertEqual(self.client.get('/servicios/gasfiteria/no-existe/').status_code, 404)

    def test_la_busqueda_libre_no_se_indexa_y_apunta_al_directorio(self):
        html = self.client.get('/servicios/?q=gasfiter').content.decode()
        self.assertIn('<meta name="robots" content="noindex, follow">', html)
        self.assertIn(f'<link rel="canonical" href="{settings.SITE_URL}/servicios/">', html)

    def test_un_perfil_nuevo_no_repite_la_comuna_en_su_slug(self):
        p = self._perfil('Cerrajero Vega Maipú', self.gasfiter, self.maipu)
        self.assertEqual(p.slug, 'cerrajero-vega-maipu')


class DatosEstructurados(Base):

    def test_la_portada_declara_la_organizacion_y_el_buscador(self):
        bloques = bloques_jsonld(self.client.get('/').content.decode())
        self.assertTrue({'Organization', 'WebSite'} <= tipos(bloques), tipos(bloques))
        sitio = next(n for b in bloques for n in b.get('@graph', [b]) if n.get('@type') == 'WebSite')
        self.assertIn('{consulta}', sitio['potentialAction']['target']['urlTemplate'])

    def test_la_organizacion_va_solo_en_la_portada(self):
        """Repetida en cada página, Google lee una entidad distinta por página."""
        p = self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        for url in (p.get_absolute_url(), '/servicios/gasfiteria/maipu/'):
            self.assertNotIn('Organization', tipos(bloques_jsonld(self.client.get(url).content.decode())))

    def test_el_listado_es_collectionpage_con_itemlist_y_miga_completa(self):
        self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        bloques = bloques_jsonld(self.client.get('/servicios/gasfiteria/maipu/').content.decode())
        self.assertTrue({'CollectionPage', 'BreadcrumbList'} <= tipos(bloques))
        miga = next(b for b in bloques if b['@type'] == 'BreadcrumbList')
        self.assertEqual([i['name'] for i in miga['itemListElement']], ['Inicio', 'Servicios', 'Gásfiter', 'Maipú'])
        lista = next(b for b in bloques if b['@type'] == 'CollectionPage')['mainEntity']
        self.assertEqual(lista['numberOfItems'], 1)

    def test_la_ficha_declara_su_tipo_de_negocio_y_la_miga_recorre_toda_la_jerarquia(self):
        p = self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        bloques = bloques_jsonld(self.client.get(p.get_absolute_url()).content.decode())
        negocio = next(b for b in bloques if b['@type'] == 'Plumber')
        self.assertEqual(negocio['address']['addressLocality'], 'Maipú')
        miga = next(b for b in bloques if b['@type'] == 'BreadcrumbList')
        self.assertEqual([i['name'] for i in miga['itemListElement']],
                         ['Inicio', 'Servicios', 'Gásfiter', 'Maipú', 'Gasfitería Uno'])

    def test_un_texto_con_script_no_rompe_el_jsonld(self):
        p = self._perfil('Gasfitería </script><script>alert(1)</script>', self.gasfiter, self.maipu)
        html = self.client.get(p.get_absolute_url()).content.decode()
        bloques_jsonld(html)  # parsea sin reventar
        self.assertNotIn('</script><script>alert(1)', html)


class SitemapYEtiquetas(Base):

    def setUp(self):
        super().setUp()
        self._perfil('Gasfitería Uno', self.gasfiter, self.maipu)
        self._perfil('Kine Ana', self.kine, self.florida)
        self._perfil('Importado', self.gasfiter, self.florida, owner=None)

    def _locs(self):
        xml = self.client.get('/sitemap.xml').content.decode()
        return [loc.replace(settings.SITE_URL, '').replace('https://testserver', '').replace('http://testserver', '')
                for loc in re.findall(r'<loc>([^<]+)</loc>', xml)]

    def test_cada_url_del_sitemap_responde_200_y_ninguna_tiene_parametros(self):
        """Regla de Jorge: el sitemap se prueba pidiendo cada <loc>."""
        locs = self._locs()
        self.assertIn('/servicios/gasfiteria/maipu/', locs)
        self.assertNotIn('/sumate/', locs, '/sumate/ es una redirección')
        for loc in locs:
            self.assertNotIn('?', loc)
            self.assertEqual(self.client.get(loc).status_code, 200, loc)

    def test_el_sitemap_no_publica_importados_ni_listados_vacios(self):
        locs = self._locs()
        self.assertFalse(any('importado' in loc for loc in locs))
        self.assertNotIn('/servicios/gasfiteria/la-florida/', locs, 'ahí solo hay un importado: está vacío')

    def test_cada_pagina_indexable_tiene_titulo_unico_un_h1_y_description(self):
        titulos = {}
        for loc in self._locs():
            html = self.client.get(loc).content.decode()
            titulo = re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()
            self.assertNotIn(titulo, titulos, f'título duplicado en {loc} y {titulos.get(titulo)}')
            titulos[titulo] = loc
            self.assertEqual(len(re.findall(r'<h1[ >]', html)), 1, f'{loc} no tiene exactamente un h1')
            description = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
            self.assertGreater(len(description), 50, loc)
            self.assertNotIn('noindex', html.split('</head>')[0], f'{loc} está en el sitemap y tiene noindex')

    def test_las_paginas_de_cuenta_no_se_indexan(self):
        """Las vistas pasaban robots=noindex y la plantilla no lo imprimía."""
        for url in (reverse('accounts:login'), reverse('accounts:register')):
            self.assertIn('<meta name="robots" content="noindex">', self.client.get(url).content.decode(), url)

    def test_hay_imagen_para_compartir_e_idioma_de_chile(self):
        html = self.client.get('/').content.decode()
        self.assertIn('<html lang="es-CL">', html)
        self.assertIn('og-serviplace.png', html)
        self.assertIn('summary_large_image', html)
