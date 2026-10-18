"""Fotos de trabajos del perfil (18-10-2026).

La ficha le decía al dueño "Todavía no subes fotos. Agregar fotos →" y el
formulario solo tenía el logo: no había dónde subirlas. Lo que se protege:
que se suban achicadas y sin la ubicación del celular (regla 12), que quitar
una borre también el archivo, que siempre haya una portada, que no pasen de
8 y que nadie pueda tocar las fotos de otro perfil.
"""
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

from accounts.forms import MAX_FOTOS
from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, ProviderImage, Region
from directory.tests_foto import foto_de_celular

User = get_user_model()
MEDIA_TMP = tempfile.mkdtemp(prefix='serviplace-test-galeria-')


@override_settings(MEDIA_ROOT=MEDIA_TMP,
                   STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class FotosDeTrabajos(TestCase):

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

    def _datos(self, **extra):
        datos = {
            'business_name': 'Gasfitería Camila', 'contact_name': 'Camila', 'category': self.cat.pk,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': 'Gásfiter en Maipú.',
            'description': 'Atiendo filtraciones y calefont en todo Maipú.', 'phone': '+56 9 8765 4321',
            'whatsapp_number': '+56 9 8765 4321', 'attends_home': 'on',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return datos

    def _publicar(self, n_fotos=0):
        fotos = [foto_de_celular(1200, 900) for _ in range(n_fotos)]
        self.client.post(reverse('accounts:provider_create'), self._datos(fotos=fotos) if fotos else self._datos())
        return Provider.objects.get(owner=self.user)

    def _editar(self, provider, **extra):
        return self.client.post(reverse('accounts:provider_edit', args=[provider.slug]), self._datos(**extra))

    def test_al_publicar_se_guardan_achicadas_sin_ubicacion_y_con_portada(self):
        p = self._publicar(3)
        imagenes = list(p.images.all())
        self.assertEqual(len(imagenes), 3)
        self.assertEqual([i.is_cover for i in imagenes].count(True), 1, 'debe haber exactamente una portada')
        self.assertTrue(imagenes[0].is_cover, 'la primera que subió es la portada')
        for imagen in imagenes:
            self.assertTrue(imagen.image.name.endswith('.webp'), imagen.image.name)
            self.assertLessEqual(imagen.image.size, 100 * 1024)
            with Image.open(imagen.image.path) as guardada:
                self.assertLessEqual(max(guardada.size), 1024)
                self.assertNotIn(0x8825, guardada.getexif(), 'la foto pública conserva el GPS del celular')

    def test_editar_quita_agrega_y_cambia_la_portada(self):
        p = self._publicar(2)
        primera, segunda = p.images.all()
        archivo_quitado = primera.image.name
        r = self._editar(p, quitar_fotos=[primera.pk], portada=segunda.pk, fotos=[foto_de_celular(800, 600)])
        self.assertEqual(r.status_code, 302)
        self.assertFalse(ProviderImage.objects.filter(pk=primera.pk).exists())
        self.assertFalse(p.images.model.image.field.storage.exists(archivo_quitado),
                         'quitar la foto dejó el archivo huérfano pagando espacio en R2')
        self.assertEqual(p.images.count(), 2)
        self.assertEqual(list(p.images.filter(is_cover=True)), [segunda])

    def test_quitar_la_portada_deja_otra_como_portada(self):
        p = self._publicar(2)
        primera, segunda = p.images.all()
        self._editar(p, quitar_fotos=[primera.pk], portada=primera.pk)
        self.assertEqual(list(p.images.filter(is_cover=True)), [segunda])

    def test_guardar_sin_tocar_las_fotos_no_las_cambia(self):
        p = self._publicar(2)
        antes = list(p.images.values_list('pk', 'is_cover', 'image'))
        self._editar(p, short_description='Gásfiter en Maipú y Cerrillos.')
        self.assertEqual(list(p.images.values_list('pk', 'is_cover', 'image')), antes)

    def test_no_pasan_de_ocho(self):
        p = self._publicar(MAX_FOTOS - 1)
        r = self._editar(p, fotos=[foto_de_celular(400, 300), foto_de_celular(400, 300)])
        self.assertEqual(r.status_code, 200)
        self.assertIn(f'Puedes tener hasta {MAX_FOTOS} fotos', r.content.decode())
        self.assertEqual(p.images.count(), MAX_FOTOS - 1, 'con el error igual se guardaron fotos')
        # Quitando una, las mismas dos sí caben.
        r = self._editar(p, quitar_fotos=[p.images.first().pk],
                         fotos=[foto_de_celular(400, 300), foto_de_celular(400, 300)])
        self.assertEqual(r.status_code, 302)
        self.assertEqual(p.images.count(), MAX_FOTOS)

    def test_un_archivo_que_no_es_imagen_se_rechaza(self):
        p = self._publicar(1)
        falso = SimpleUploadedFile('trabajo.jpg', b'esto no es una imagen', content_type='image/jpeg')
        r = self._editar(p, fotos=[falso])
        self.assertIn('No pudimos leer ese archivo como imagen', r.content.decode())
        self.assertEqual(p.images.count(), 1)

    def test_no_se_pueden_quitar_ni_marcar_fotos_de_otro_perfil(self):
        """G-02: el formulario recibe ids; un id ajeno no puede borrar nada."""
        otro_user = User.objects.create_user('ajeno', password='clave-larga-de-verdad-99')
        ajeno = Provider.objects.create(
            owner=otro_user, business_name='Otro', category=self.cat, commune=self.maipu,
            short_description='x', whatsapp_number='+56911111111', is_active=True)
        foto_ajena = ProviderImage.objects.create(provider=ajeno, image='providers/ajena.webp', is_cover=True)
        p = self._publicar(1)
        self._editar(p, quitar_fotos=[foto_ajena.pk], portada=foto_ajena.pk)
        foto_ajena.refresh_from_db()
        self.assertTrue(foto_ajena.is_cover)
        self.assertEqual(foto_ajena.provider, ajeno)
        self.assertTrue(p.images.get().is_cover, 'marcar una foto ajena le quitó la portada a la propia')

    def test_la_ficha_y_la_tarjeta_las_muestran(self):
        p = self._publicar(2)
        portada = p.images.get(is_cover=True)
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        for imagen in p.images.all():
            self.assertIn(imagen.image.url, ficha)
        self.assertNotIn('Todavía no subes fotos', ficha)
        self.assertIn(portada.image.url, self.client.get(reverse('directory:provider_list')).content.decode())

    def test_el_aviso_de_la_ficha_lleva_a_la_seccion_de_fotos(self):
        p = self._publicar()
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        destino = reverse('accounts:provider_edit', args=[p.slug]) + '#fotos'
        self.assertIn(destino, ficha)
        formulario = self.client.get(destino.split('#')[0]).content.decode()
        self.assertIn('id="fotos"', formulario)
        self.assertRegex(formulario, r'<input[^>]*name="fotos"[^>]*multiple|<input[^>]*multiple[^>]*name="fotos"')

    def test_el_formulario_de_editar_muestra_cada_foto_con_portada_y_quitar(self):
        p = self._publicar(2)
        html = self.client.get(reverse('accounts:provider_edit', args=[p.slug])).content.decode()
        for imagen in p.images.all():
            self.assertIn(f'name="portada" value="{imagen.pk}"', html)
            self.assertIn(f'name="quitar_fotos" value="{imagen.pk}"', html)
        self.assertIn('Así se verá tu tarjeta', html)

    def test_la_ficha_es_una_galeria_que_abre_cada_foto(self):
        """18-10-2026: "las fotos no las puedo ver, como galería"."""
        p = self._publicar(5)
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('id="galeria-visor"', ficha)
        self.assertIn('data-n="3"', ficha)
        self.assertIn('+2 fotos', ficha)
        for imagen in p.images.all():
            self.assertIn(f'href="{imagen.image.url}" data-galeria-foto', ficha,
                          'cada foto debe ser un enlace: sin JavaScript igual se abre')
        self.assertIn('data-visor="next"', ficha)

    def test_con_una_sola_foto_el_visor_no_tiene_flechas(self):
        p = self._publicar(1)
        ficha = self.client.get(p.get_absolute_url()).content.decode()
        self.assertIn('id="galeria-visor"', ficha)
        self.assertIn('data-n="1"', ficha)
        self.assertNotIn('data-visor="next"', ficha)

    def test_el_aviso_de_que_faltan_fotos_solo_lo_ve_el_dueno(self):
        """Se lo mostraba a cualquier visitante de un perfil con dueño."""
        p = self._publicar()
        self.assertIn('Todavía no subes fotos', self.client.get(p.get_absolute_url()).content.decode())
        self.client.logout()
        self.assertNotIn('Todavía no subes fotos', self.client.get(p.get_absolute_url()).content.decode())
        otro = User.objects.create_user('visita', password='clave-larga-de-verdad-99')
        self.client.force_login(otro)
        self.assertNotIn('Todavía no subes fotos', self.client.get(p.get_absolute_url()).content.decode())
