"""Logo o foto del perfil (18-10-2026).

Lo que se protege: que la imagen pública nunca lleve la ubicación del
celular, que pese poco (regla 12: WebP < 100 KB), que un archivo cualquiera
no se cuele como imagen y que reemplazarla no deje huérfanos en R2.
"""
import io
import shutil
import tempfile
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()
MEDIA_TMP = tempfile.mkdtemp(prefix='serviplace-test-media-')


def foto_de_celular(ancho=3000, alto=2000, con_gps=True):
    """Un JPEG grande como el de un teléfono, con EXIF de ubicación."""
    imagen = Image.new('RGB', (ancho, alto), (200, 120, 90))
    exif = Image.Exif()
    exif[0x010F] = 'TelefonoDePrueba'  # Make
    if con_gps:
        exif[0x8825] = {1: 'S', 2: (33.0, 30.0, 0.0), 3: 'W', 4: (70.0, 45.0, 0.0)}  # GPSInfo
    salida = io.BytesIO()
    imagen.save(salida, 'JPEG', quality=95, exif=exif)
    return SimpleUploadedFile('foto.jpg', salida.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA_TMP,
                   STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class LogoOFoto(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = Category.objects.get(slug='gasfiteria')
        self.user = User.objects.create_user('camila', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def _publicar(self, foto=None, **extra):
        datos = {
            'business_name': 'Gasfitería Camila', 'contact_name': 'Camila', 'category': self.cat.pk,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': 'Gásfiter en Maipú.',
            'description': 'Atiendo filtraciones y calefont en todo Maipú.', 'phone': '+56 9 8765 4321',
            'whatsapp_number': '+56 9 8765 4321', 'attends_home': 'on',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        if foto is not None:
            datos['foto'] = foto
        datos.update(extra)
        return self.client.post(reverse('accounts:provider_create'), datos)

    def test_se_guarda_achicada_en_webp_y_sin_la_ubicacion(self):
        self._publicar(foto_de_celular())
        p = Provider.objects.get(owner=self.user)
        self.assertTrue(p.foto.name.endswith('.webp'), p.foto.name)
        self.assertLessEqual(p.foto.size, 100 * 1024)
        with Image.open(p.foto.path) as guardada:
            self.assertLessEqual(max(guardada.size), 640)
            self.assertEqual(guardada.format, 'WEBP')
            exif = guardada.getexif()
            self.assertNotIn(0x8825, exif, 'la foto pública conserva el GPS del celular')
            self.assertNotIn(0x010F, exif)

    def test_un_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile('foto.jpg', b'esto no es una imagen', content_type='image/jpeg')
        r = self._publicar(falso)
        self.assertFalse(Provider.objects.filter(owner=self.user).exists())
        self.assertIn('No pudimos leer ese archivo como imagen', r.content.decode())

    def test_reemplazarla_borra_la_anterior(self):
        """Si no, cada cambio deja un archivo huérfano pagando espacio en R2."""
        self._publicar(foto_de_celular(800, 600))
        p = Provider.objects.get(owner=self.user)
        anterior = p.foto.name
        datos = {
            'business_name': p.business_name, 'contact_name': p.contact_name, 'category': self.cat.pk,
            'commune': self.maipu.pk, 'sector': p.sector, 'short_description': p.short_description,
            'description': p.description, 'phone': p.phone, 'whatsapp_number': '+56 9 8765 4321',
            'attends_home': 'on', 'foto': foto_de_celular(900, 700),
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        self.client.post(reverse('accounts:provider_edit', args=[p.slug]), datos)
        p.refresh_from_db()
        self.assertNotEqual(p.foto.name, anterior)
        self.assertFalse(p.foto.storage.exists(anterior), 'la foto anterior quedó huérfana')

    def test_la_tarjeta_y_la_ficha_la_muestran(self):
        self._publicar(foto_de_celular(800, 600))
        p = Provider.objects.get(owner=self.user)
        self.assertIn(p.foto.url, self.client.get(reverse('directory:provider_list')).content.decode())
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn(p.foto.url, ficha)
        self.assertIn('og:image', ficha, 'al compartir por WhatsApp no se vería la foto')

    def test_solo_con_foto_se_puede_ser_destacado(self):
        self._publicar()
        self.assertNotIn('Perfiles destacados', self.client.get(reverse('core:home')).content.decode())
        p = Provider.objects.get(owner=self.user)
        p.foto = foto_de_celular(400, 400)
        p.save()
        self.assertIn('Perfiles destacados', self.client.get(reverse('core:home')).content.decode())
