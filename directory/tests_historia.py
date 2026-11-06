"""Historia de Instagram con la ficha (02-11-2026).

Diego: "una ficha para compartir fácil en IG como storie, y que eso se
pegue". Lo que se protege: que la imagen tenga el tamaño de una historia,
que salgan la foto y los trabajos (lo que convence), que un dato cambiado o
un sello nuevo no deje servida la imagen vieja, que un archivo perdido o un
emoji no dejen al profesional sin historia, que solo exista para perfiles
públicos, y que quien llega desde una historia vea la invitación a publicar.
"""
import io
import shutil
import tempfile
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from directory import historia
from directory.models import Category, Commune, Provider, ProviderImage, Region

User = get_user_model()
MEDIA_TMP = tempfile.mkdtemp(prefix='serviplace-test-historia-')
ROJO, AZUL = (220, 30, 30), (20, 60, 220)


def png(color, lado=400):
    salida = io.BytesIO()
    Image.new('RGB', (lado, lado), color).save(salida, 'PNG')
    return ContentFile(salida.getvalue())


def pixeles_de(datos, color, tolerancia=40):
    """Cuántos píxeles de la imagen se parecen a `color` (el JPEG los mueve un poco)."""
    imagen = Image.open(io.BytesIO(datos)).convert('RGB')
    return sum(n for n, c in imagen.getcolors(maxcolors=1 << 24)
               if all(abs(a - b) <= tolerancia for a, b in zip(c, color)))


@override_settings(MEDIA_ROOT=MEDIA_TMP,
                   STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class HistoriaDeInstagram(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def setUp(self):
        cache.clear()  # la imagen se guarda por versión: entre pruebas no se arrastra
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = Category.objects.get(slug='gasfiteria')
        self.dueno = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.p = Provider.objects.create(
            owner=self.dueno, business_name='Gasfitería Camila', category=self.cat, commune=self.maipu,
            sector='Ciudad Satélite', short_description='Calefont, filtraciones y destapes en Maipú.',
            whatsapp_number='56987654321', attends_home=True, is_active=True)

    def _historia(self, provider=None, **params):
        return self.client.get(reverse('directory:historia', args=[(provider or self.p).slug]), params)

    def test_es_una_imagen_vertical_del_tamano_de_una_historia(self):
        respuesta = self._historia()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'image/jpeg')
        self.assertEqual(Image.open(io.BytesIO(respuesta.content)).size, (1080, 1920))
        self.assertIn('noindex', respuesta['X-Robots-Tag'])

    def test_solo_existe_para_perfiles_publicos(self):
        sin_dueno = Provider.objects.create(
            business_name='Importado de Maps', category=self.cat, commune=self.maipu,
            short_description='Sin dueño.', whatsapp_number='56911111111', is_active=True)
        self.assertEqual(self._historia(sin_dueno).status_code, 404)
        Provider.objects.filter(pk=self.p.pk).update(is_active=False)
        self.assertEqual(self._historia().status_code, 404)

    def test_con_la_version_vigente_el_navegador_la_guarda_un_dia(self):
        vigente = self._historia(v=self.p.version_historia)
        self.assertIn('max-age=86400', vigente['Cache-Control'])
        vieja = self._historia(v='otra')
        self.assertIn('max-age=300', vieja['Cache-Control'])

    def test_la_version_cambia_con_lo_que_se_dibuja_y_no_con_las_visitas(self):
        inicial = self.p.version_historia
        Provider.objects.filter(pk=self.p.pk).update(views_count=50, whatsapp_clicks_count=3)
        self.assertEqual(Provider.objects.get(pk=self.p.pk).version_historia, inicial)
        # El sello se da con .update(), que no toca updated_at: igual tiene que cambiarla.
        Provider.objects.filter(pk=self.p.pk).update(whatsapp_confirmado_en=timezone.now())
        con_sello = Provider.objects.get(pk=self.p.pk).version_historia
        self.assertNotEqual(con_sello, inicial)
        Provider.objects.filter(pk=self.p.pk).update(business_name='Camila Gásfiter')
        self.assertNotEqual(Provider.objects.get(pk=self.p.pk).version_historia, con_sello)

    def test_no_redibuja_mientras_la_version_no_cambie(self):
        with mock.patch('directory.views.dibujar_historia', wraps=historia.dibujar) as dibujo:
            self._historia()
            self._historia()
            self.assertEqual(dibujo.call_count, 1)
            Provider.objects.filter(pk=self.p.pk).update(whatsapp_confirmado_en=timezone.now())
            self._historia()
            self.assertEqual(dibujo.call_count, 2)

    def test_salen_la_foto_y_las_fotos_de_trabajos(self):
        sin_fotos = self._historia().content
        self.p.foto.save('logo.png', png(ROJO))
        trabajo = ProviderImage(provider=self.p)
        trabajo.image.save('trabajo.png', png(AZUL))
        con_fotos = self._historia().content
        self.assertEqual(pixeles_de(sin_fotos, ROJO), 0)
        self.assertEqual(pixeles_de(sin_fotos, AZUL), 0)
        self.assertGreater(pixeles_de(con_fotos, ROJO), 10000)   # el círculo de 164 px
        self.assertGreater(pixeles_de(con_fotos, AZUL), 40000)   # el cuadrado de 258 px

    def test_un_archivo_perdido_no_deja_al_profesional_sin_historia(self):
        Provider.objects.filter(pk=self.p.pk).update(foto='perfiles/2026/11/no-existe.webp')
        trabajo = ProviderImage.objects.create(provider=self.p, image='providers/tampoco-existe.webp')
        respuesta = self._historia()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Image.open(io.BytesIO(respuesta.content)).size, (1080, 1920))
        trabajo.delete()

    def test_emojis_y_textos_largos_no_rompen_la_imagen(self):
        Provider.objects.filter(pk=self.p.pk).update(
            business_name='Gasfitería Camila 🔧🚿 Servicio Técnico Integral Las 24 Horas del Día',
            profession_title='Instaladora de gas certificada con muchos años de experiencia en la comuna',
            short_description='Destapes ' * 30)
        self.assertEqual(self._historia().status_code, 200)
        self.assertEqual(historia._limpio('Camila 🔧 Gásfiter ✨'), 'Camila Gásfiter')

    def test_el_texto_largo_termina_en_puntos_suspensivos_sin_salirse(self):
        fuente = historia._fuente(historia.TEXTO, 38)
        lineas = historia._partir('palabra ' * 80, fuente, 500, 3)
        self.assertEqual(len(lineas), 3)
        self.assertTrue(lineas[-1].endswith('…'))
        self.assertTrue(all(fuente.getlength(linea) <= 500 for linea in lineas))
        largo = historia._partir('Supercalifragilisticoespialidoso' * 3, fuente, 300, 5)
        self.assertTrue(all(fuente.getlength(linea) <= 300 for linea in largo))

    def test_la_ficha_ofrece_compartirla_con_el_enlace_marcado(self):
        html = self.client.get(self.p.get_absolute_url()).content.decode()
        self.assertIn(f'data-historia-abrir="historia-{self.p.slug}"', html)
        self.assertIn(self.p.url_historia, html)
        self.assertIn('utm_source=instagram&amp;utm_medium=historia', html)

    def test_cualquier_visitante_la_ve_arriba_sin_ser_el_dueno(self):
        # 03-11: abajo quedaba a dos pantallas y parecía cosa del dueño.
        html = self.client.get(self.p.get_absolute_url()).content.decode()
        boton = f'data-historia-abrir="historia-{self.p.slug}"'
        self.assertEqual(html.count(boton), 2)  # arriba y en "Compartir este perfil"
        self.assertEqual(html.count(f'<dialog class="historia-dialogo" id="historia-{self.p.slug}"'), 1)
        self.assertLess(html.index(boton), html.index('Sobre este servicio'))

    def test_quien_llega_desde_una_historia_ve_la_invitacion_a_publicar(self):
        invitacion = '¿Tú también ofreces un servicio?'
        self.assertNotContains(self.client.get(self.p.get_absolute_url()), invitacion)
        desde_historia = self.client.get(self.p.get_absolute_url(), {'utm_medium': 'historia'})
        self.assertContains(desde_historia, invitacion)
        self.assertContains(desde_historia, reverse('core:para_profesionales'))
        # 06-11: abajo (2,2 pantallas en el celular) nadie la tocó en 44 visitas.
        html = desde_historia.content.decode()
        self.assertLess(html.index(invitacion), html.index('Sobre este servicio'))

    def test_el_panel_la_ofrece_solo_para_los_perfiles_publicos(self):
        apagado = Provider.objects.create(
            owner=self.dueno, business_name='Perfil apagado', category=self.cat, commune=self.maipu,
            short_description='No se muestra.', whatsapp_number='56922222222', is_active=False)
        self.client.force_login(self.dueno)
        html = self.client.get(reverse('accounts:dashboard')).content.decode()
        self.assertIn(f'data-historia-abrir="historia-{self.p.slug}"', html)
        self.assertNotIn(f'data-historia-abrir="historia-{apagado.slug}"', html)

    def _otro(self, nombre, **extra):
        return Provider.objects.create(
            owner=self.dueno, business_name=nombre, category=self.cat, commune=self.maipu,
            short_description='Otro servicio.', whatsapp_number='56933333333', **dict({'is_active': True}, **extra))

    def test_la_pagina_de_historias_es_solo_del_staff_y_trae_cada_ficha_publica(self):
        apagado = self._otro('Perfil apagado', is_active=False)
        url = reverse('accounts:historias')
        self.assertEqual(self.client.get(url).status_code, 302)  # sin sesión: al login
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(url).status_code, 404)  # un profesional no la ve
        self.client.force_login(User.objects.create_user('diego', password='otra-clave-larga-99', is_staff=True))
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, self.p.url_historia)
        self.assertContains(respuesta, f'<dialog class="historia-dialogo" id="historia-{self.p.slug}"')
        self.assertContains(respuesta, self.p.enlace_historia.replace('&', '&amp;'))
        self.assertNotContains(respuesta, f'historia-{apagado.slug}')
        self.assertContains(respuesta, 'noindex')

    def test_la_pagina_de_historias_no_hace_una_consulta_por_ficha(self):
        self.client.force_login(User.objects.create_user('diego', password='otra-clave-larga-99', is_staff=True))
        url = reverse('accounts:historias')
        self.client.get(url)  # lo que se carga una sola vez por sesión
        with CaptureQueriesContext(connection) as con_una:
            self.client.get(url)
        otro_rubro = Category.objects.exclude(pk=self.cat.pk).first()
        for i, color in enumerate((ROJO, AZUL)):
            otro = self._otro(f'Otro {i}')
            otro.otras_categorias.add(otro_rubro)
            ProviderImage(provider=otro).image.save(f'trabajo-{i}.png', png(color))
        with CaptureQueriesContext(connection) as con_tres:
            self.client.get(url)
        self.assertEqual(len(con_tres), len(con_una))
