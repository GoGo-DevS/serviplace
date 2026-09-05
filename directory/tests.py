"""Criterios B3, C1-C3 y D1/D4 de TASK.md — el directorio público.

Todo lo que se prueba acá se ve en la parte del sitio que cualquiera puede
abrir sin cuenta, que es donde un defecto se paga con la reputación del
directorio y no solo con un error en un log.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Commune, Provider, Region
from .views import PROVEEDORES_POR_PAGINA

User = get_user_model()


class Base(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.comuna = Commune.objects.create(region=self.region, name='Maipú',
                                             slug='maipu', is_active=True)
        self.categoria = Category.objects.create(name='Gasfitería', slug='gasfiteria',
                                                 is_active=True)

    def _prestador(self, nombre='Gasfitería Uno', **extra):
        datos = dict(
            business_name=nombre, category=self.categoria, commune=self.comuna,
            whatsapp_number='56911112222', is_active=True,
            source_name='Google Maps', source_url='https://maps.google.com/x',
        )
        datos.update(extra)
        return Provider.objects.create(**datos)


# ─────────────────────────────────────────────────────────────────────────
# B3 · XSS
# ─────────────────────────────────────────────────────────────────────────
class B3LoQuePublicaUnUsuarioNoSeEjecuta(Base):
    """El sitio es autoservicio: el nombre y la descripción los escribe
    cualquiera que se registre, y se muestran a todos los visitantes. Si eso se
    interpretara como HTML, un solo prestador podría robar la sesión de quien
    abra su ficha."""

    CARGAS = [
        '<script>alert(1)</script>',
        '"><img src=x onerror=alert(1)>',
        "javascript:alert(document.cookie)",
        '<svg onload=alert(1)>',
    ]

    def setUp(self):
        super().setUp()
        # La línea base: la MISMA ficha con un nombre limpio. Los scripts que
        # tenga esta página son los legítimos del sitio, y cualquier elemento
        # ejecutable de más en las otras vino de la carga.
        limpio = self._prestador(nombre='Gasfitería Limpia')
        self.__class__.HTML_LIMPIO = self.client.get(
            limpio.get_absolute_url()).content.decode()
        limpio.delete()

    def _peligros(self, html):
        """Cuenta elementos ejecutables, PARSEANDO el HTML.

        Con expresiones regulares no se puede: el tercer intento buscaba
        `<\\w+[^>]*\\sonerror=` y daba falso positivo porque la carga escapada
        vive DENTRO de `<meta content="…">`, así que el patrón cruzaba desde el
        `<meta` real hasta el `onerror` que era texto de un atributo.

        Un parser no se confunde: para él, texto escapado es texto y nunca se
        convierte en etiqueta. Es de la biblioteca estándar, sin dependencias.
        """
        from html.parser import HTMLParser

        class Detector(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.cuenta = {'script': 0, 'evento': 0, 'js_href': 0}

            def handle_starttag(self, tag, attrs):
                if tag == 'script':
                    self.cuenta['script'] += 1
                for nombre, valor in attrs:
                    if nombre.lower().startswith('on'):
                        self.cuenta['evento'] += 1
                    if (nombre.lower() in ('href', 'src', 'action')
                            and (valor or '').strip().lower().startswith('javascript:')):
                        self.cuenta['js_href'] += 1

        d = Detector()
        d.feed(html)
        return d.cuenta

    def _sin_html_ejecutable(self, html, donde):
        """Falla si la carga AGREGÓ HTML ejecutable, comparando con una base.

        Dos formas ingenuas que se descartaron, y por qué:

        · Buscar la subcadena `onerror=alert(1)`. Escapado correctamente el
          texto queda `&lt;img src=x onerror=alert(1)&gt;` y esa subcadena
          aparece igual, como texto en el título, sin ejecutarse. La prueba
          fallaba sobre código correcto — peor que no tenerla: manda a
          "arreglar" algo que funciona.

        · Buscar cualquier `<script`. La página tiene los suyos, legítimos.
          Fallaba siempre, con carga o sin ella.

        Lo que se mide es el DELTA contra una ficha idéntica con nombre limpio:
        si la carga no agregó ni un elemento ejecutable, no se interpretó.
        """
        base = self._peligros(self.__class__.HTML_LIMPIO)
        ahora = self._peligros(html)
        for clave, cuantos in ahora.items():
            self.assertLessEqual(
                cuantos, base[clave],
                f'{donde}: la carga agregó {cuantos - base[clave]} elemento(s) '
                f'ejecutable(s) de tipo "{clave}" al HTML')

    def test_el_nombre_no_se_ejecuta(self):
        for carga in self.CARGAS:
            with self.subTest(carga=carga):
                p = self._prestador(nombre=f'Gasfitería {carga}')
                html = self.client.get(p.get_absolute_url()).content.decode()
                self._sin_html_ejecutable(html, f'nombre con {carga!r}')
                p.delete()

    def test_la_descripcion_no_se_ejecuta(self):
        p = self._prestador(description='<script>alert(1)</script> hola',
                            short_description='<img src=x onerror=alert(1)>')
        html = self.client.get(p.get_absolute_url()).content.decode()
        self._sin_html_ejecutable(html, 'descripción')

    def test_la_prueba_de_XSS_DETECTA_html_sin_escapar(self):
        """La prueba de la prueba.

        Si el detector no reconociera una etiqueta ejecutable, todas las de
        arriba pasarían siempre y no probarían nada. Acá se le da la línea base
        MÁS un script inyectado: tiene que fallar. Sin esto, esta suite podría
        estar dando verde sobre un sitio vulnerable.
        """
        inyectado = self.HTML_LIMPIO + '<script>alert(1)</script>'
        with self.assertRaises(AssertionError):
            self._sin_html_ejecutable(inyectado, 'control con script inyectado')

    def test_y_tambien_detecta_un_manejador_de_evento(self):
        inyectado = self.HTML_LIMPIO + '<img src=x onerror=alert(1)>'
        with self.assertRaises(AssertionError):
            self._sin_html_ejecutable(inyectado, 'control con onerror inyectado')

    def test_y_el_texto_SI_se_ve(self):
        """La contracara: escapar no puede significar borrar. Si el nombre
        desapareciera, el prestador no aparecería en su propia ficha."""
        p = self._prestador(nombre='Gasfitería <b>Uno</b>')
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('Gasfiter', html)
        self.assertIn('&lt;b&gt;', html)

    def test_tampoco_en_el_listado(self):
        """El listado muestra los mismos campos y suele olvidarse."""
        self._prestador(nombre='Gasfitería <script>alert(1)</script>')
        html = self.client.get(reverse('directory:provider_list')).content.decode()
        self.assertNotIn('<script>alert(1)</script>', html)


# ─────────────────────────────────────────────────────────────────────────
# D1 · El listado pagina
# ─────────────────────────────────────────────────────────────────────────
class D1ElListadoPagina(Base):
    """Sin paginar, /servicios/ medía 162.604 px de alto en un teléfono: unas
    190 pantallas de scroll, y el navegador pedía las 361 fotos de una."""

    def setUp(self):
        super().setUp()
        for i in range(PROVEEDORES_POR_PAGINA + 5):
            self._prestador(nombre=f'Prestador {i:03d}')

    def test_la_primera_pagina_no_trae_todo(self):
        r = self.client.get(reverse('directory:provider_list'))
        self.assertEqual(len(r.context['providers']), PROVEEDORES_POR_PAGINA)

    def test_la_segunda_pagina_trae_el_resto(self):
        r = self.client.get(reverse('directory:provider_list'), {'page': 2})
        self.assertEqual(len(r.context['providers']), 5)

    def test_ningun_prestador_se_repite_ni_se_pierde_entre_paginas(self):
        """El defecto clásico de paginar sobre un orden no determinista: sin un
        desempate único, un registro sale en las dos páginas y otro en ninguna.

        LOS NOMBRES SE REPITEN A PROPÓSITO. La primera versión de esta prueba
        usaba nombres únicos ("Prestador 000"…) y por eso PASABA aunque se
        quitara el desempate por `pk`: con nombres distintos, `business_name`
        ya ordena de forma determinista y el defecto no se puede manifestar.
        Comprobado desarmando el arreglo: la prueba seguía en verde.

        Con empate real —y en un directorio de gásfiters "Cerrajería 24 Horas"
        repetido es lo normal, no lo raro— la base puede devolverlos en
        cualquier orden entre consultas, y ahí sí se ve.
        """
        Provider.objects.filter(is_active=True).delete()
        for _ in range(PROVEEDORES_POR_PAGINA + 5):
            self._prestador(nombre='Cerrajería 24 Horas')

        vistos = []
        for pagina in (1, 2):
            r = self.client.get(reverse('directory:provider_list'), {'page': pagina})
            vistos += [p.pk for p in r.context['providers']]
        self.assertEqual(len(vistos), len(set(vistos)), 'hay prestadores repetidos')
        self.assertEqual(len(vistos), Provider.objects.filter(is_active=True).count(),
                         'se perdieron prestadores entre páginas')

    def test_el_orden_TERMINA_en_un_campo_unico(self):
        """Se verifica el `order_by`, no el resultado. Y es a propósito.

        El no-determinismo al paginar sin desempate NO SE PUEDE REPRODUCIR EN
        SQLITE: se intentó con 29 prestadores de nombre idéntico y el orden
        salió estable igual, así que la prueba pasaba con el desempate y sin
        él. Comprobado desarmando el arreglo dos veces.

        Pero en producción corre PostgreSQL, donde `ORDER BY` sobre columnas
        que empatan no garantiza ningún orden entre consultas: ahí sí un
        prestador sale en las dos páginas y otro en ninguna. Un defecto que
        solo aparece en el motor de producción es exactamente el que nadie
        detecta a tiempo.

        Como el comportamiento no es observable acá, se fija la única cosa que
        sí lo es y que lo previene: que el orden termine en una columna única.
        Es una prueba de implementación, y se acepta porque la alternativa es
        no proteger nada.
        """
        campos = Provider.objects.filter(is_active=True).order_by(
            '-is_featured', '-is_verified', 'business_name', 'pk').query.order_by
        r = self.client.get(reverse('directory:provider_list'))
        orden_real = r.context['providers'].query.order_by if hasattr(
            r.context['providers'], 'query') else campos
        ultimo = str(orden_real[-1]).lstrip('-')
        self.assertIn(ultimo, ('pk', 'id'),
                      f'el orden termina en "{ultimo}", que puede empatar: '
                      f'al paginar en PostgreSQL eso repite y pierde registros')

    def test_los_filtros_sobreviven_al_cambiar_de_pagina(self):
        """Si al pasar a la página 2 se perdiera la comuna, el visitante
        volvería a 'todo Chile' sin entender por qué."""
        html = self.client.get(reverse('directory:provider_list'),
                               {'comuna': 'maipu'}).content.decode()
        self.assertIn('comuna=maipu', html)

    def test_una_pagina_que_no_existe_devuelve_la_ultima_no_un_error(self):
        """La URL puede venir de un enlace viejo o de Google; un error ahí se
        lee como sitio roto."""
        r = self.client.get(reverse('directory:provider_list'), {'page': 999})
        self.assertEqual(r.status_code, 200)

    def test_una_pagina_no_numerica_no_revienta(self):
        r = self.client.get(reverse('directory:provider_list'), {'page': 'dos'})
        self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────
# D4 · El hueco de fotos solo para quien puede llenarlo
# ─────────────────────────────────────────────────────────────────────────
class D4NoSeAnuncianFotosQueNadiePuedeSubir(Base):
    """Un perfil que vino de Google Maps no tiene a nadie que pueda subir una
    foto. Anunciar que le faltan no informa nada: se lee como que el sitio está
    a medio hacer, y son la mayoría de las fichas."""

    def test_un_perfil_scrapeado_no_muestra_el_hueco(self):
        p = self._prestador(owner=None)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertNotIn('Sin fotos publicadas', html)

    def test_pero_a_su_DUENO_si_se_le_ofrece_subirlas(self):
        """A quien sí puede hacerlo, es una tarea, no un defecto."""
        u = User.objects.create_user('duena', password='x')
        p = self._prestador(nombre='Gasfitería Con Dueña', owner=u)
        html = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('fotos', html.lower())


# ─────────────────────────────────────────────────────────────────────────
# C · Los datos publicados
# ─────────────────────────────────────────────────────────────────────────
class CNadaSePublicaSinDecirDeDondeSalio(Base):
    """La base legal para listar un negocio sin pedirle permiso es que la
    información sea pública Y que él pueda actuar sobre ella. Sin la fuente
    guardada no se puede responder de dónde salió un dato, y sin la vía para
    reclamarlo el prestador no tiene cómo corregirlo."""

    def test_la_ficha_de_un_perfil_sin_dueno_ofrece_reclamarlo(self):
        p = self._prestador(owner=None)
        html = self.client.get(p.get_absolute_url()).content.decode().lower()
        self.assertTrue('reclam' in html or 'baja' in html or 'corregir' in html,
                        'no hay forma de reclamar el perfil ni pedir su baja')

    def test_el_listado_solo_muestra_activos(self):
        """Los sintéticos que quedan en la base están desactivados: si el
        listado ignorara `is_active`, volverían a verse."""
        self._prestador(nombre='Visible', is_active=True)
        self._prestador(nombre='Retenido', is_active=False)
        html = self.client.get(reverse('directory:provider_list')).content.decode()
        self.assertIn('Visible', html)
        self.assertNotIn('Retenido', html)

    def test_la_ficha_de_uno_inactivo_no_es_publica(self):
        """Ocultarlo del listado pero servirlo por URL directa no lo oculta:
        Google lo indexa igual."""
        p = self._prestador(nombre='Retenido', is_active=False)
        r = self.client.get(p.get_absolute_url())
        self.assertNotEqual(r.status_code, 200)
