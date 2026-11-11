"""Guardar el perfil con fotos daba 502 (11-11-2026).

Manitos Curiosas: "se cae al ingresar cosas al perfil". En Render (plan
gratis, una décima de CPU) el worker sync de gunicorn tiene 30 s: una subida
lenta de varias fotos de celular, más procesarlas a tamaño completo, los
pasaba y Render respondía 502. Lo que se protege:
- la foto se decodifica ya reducida (draft) y sigue saliendo derecha;
- gunicorn usa hilos y 120 s de límite;
- el formulario achica las fotos en el teléfono antes de subirlas.
"""
import io
import runpy
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from PIL import Image, JpegImagePlugin

from directory.imagenes import procesar_foto
from directory.models import Commune, Region


def foto_girada(ancho=4000, alto=3000):
    """JPEG apaisado guardado con la marca EXIF 'girar 90°' (orientación 6),
    como las fotos verticales que guarda un teléfono."""
    imagen = Image.new('RGB', (ancho, alto), (30, 140, 200))
    exif = Image.Exif()
    exif[0x0112] = 6
    salida = io.BytesIO()
    imagen.save(salida, 'JPEG', quality=90, exif=exif)
    return SimpleUploadedFile('vertical.jpg', salida.getvalue(), content_type='image/jpeg')


class FotoRapida(SimpleTestCase):

    def test_el_jpeg_se_decodifica_ya_reducido(self):
        with mock.patch.object(JpegImagePlugin.JpegImageFile, 'draft', autospec=True,
                               side_effect=JpegImagePlugin.JpegImageFile.draft) as draft:
            procesar_foto(foto_girada(), lado_maximo=1024)
        draft.assert_called_once()
        self.assertEqual(draft.call_args.args[2], (2048, 2048))

    def test_reducida_sigue_saliendo_derecha_liviana_y_del_tamano_justo(self):
        resultado = Image.open(io.BytesIO(procesar_foto(foto_girada(), lado_maximo=1024).read()))
        self.assertEqual(resultado.format, 'WEBP')
        self.assertEqual(resultado.size, (768, 1024))  # vertical: la marca EXIF se respetó

    def test_un_png_tambien_pasa(self):
        salida = io.BytesIO()
        Image.new('RGBA', (3000, 3000), (0, 0, 0, 0)).save(salida, 'PNG')
        resultado = procesar_foto(SimpleUploadedFile('logo.png', salida.getvalue(), content_type='image/png'))
        self.assertEqual(Image.open(io.BytesIO(resultado.read())).size, (640, 640))


class GunicornAguantaSubidasLentas(SimpleTestCase):

    def test_hilos_y_120_segundos(self):
        conf = runpy.run_path(str(Path(settings.BASE_DIR) / 'gunicorn.conf.py'))
        self.assertEqual(conf['worker_class'], 'gthread')
        self.assertGreaterEqual(conf['timeout'], 120)
        self.assertGreaterEqual(conf['threads'], 2)


class FormularioAchicaEnElTelefono(TestCase):

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.client.force_login(get_user_model().objects.create_user('ana', password='clave-larga-de-verdad-99'))

    def test_el_formulario_trae_el_achicador_para_logo_y_fotos(self):
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('var LADOS = {id_foto: 1280, id_fotos: 2048};', html)
        self.assertIn('id="id_foto"', html)
        self.assertIn('id="id_fotos"', html)
