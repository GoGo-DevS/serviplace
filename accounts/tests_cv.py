"""El CV que llena el perfil (18-10-2026).

Lo que se prueba es lo que importa: que lo que se propone sea de ESA persona,
que lo privado del CV (dirección, RUT, correo) no llegue al perfil público, y
que el archivo no se guarde en ninguna parte.
"""
import io
import shutil
import tempfile
import time
import zipfile
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.cv import CVIlegible, extraer_texto, proponer_perfil
from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()

CV_KINE = """CURRICULUM VITAE
CAMILA ANDREA ROJAS SOTO
Kinesióloga
RUT: 18.765.432-1
Dirección: Pasaje Los Aromos 1234, Lomas de San Andrés, Concepción
Celular: +56 9 8765 4321
Correo: camila.rojas.kine@gmail.com

PERFIL PROFESIONAL
Kinesióloga titulada de la Universidad de Concepción, con experiencia en rehabilitación
musculoesquelética y adulto mayor. Realizo atención a domicilio y telerehabilita-
ción para pacientes que no pueden trasladarse.

FORMACIÓN ACADÉMICA
2014 – 2019
Kinesiología
Universidad de Concepción
2021
Diplomado en Kinesiología Geriátrica, Pontificia Universidad Católica de Chile

EXPERIENCIA LABORAL
2020 – 2023 Kinesióloga, Dirección de Salud Municipal de Maipú
Atención de pacientes junto a enfermeras y kinesiólogos del equipo.

OTROS ANTECEDENTES
Registro Superintendencia de Salud N° 654321
Idiomas: Inglés intermedio
Intereses: música, pintura y trekking
"""

CV_GASFITER = """Juan Pérez Muñoz
Maestro gásfiter
Vivo en Maipú · +56 9 1234 5678 · juan.santiago@gmail.com

Experiencia
Gasfitería residencial, calefont y destapes desde 2009.
Estudios
Liceo Industrial de Maipú
Curso de instalador de gas SEC, 2015
"""

CV_ESTUDIANTE = """Valentina Muñoz
Estudiante de Psicología
Comuna: Ñuñoa
Formación
Psicología, Universidad de Santiago de Chile, 2021 – actualidad
Experiencia
Ayudante de cátedra de Psicología del Desarrollo 2023.
Tutora de matemáticas para escolares.
Otros
Disponibilidad inmediata. Me gusta la música y la lectura.
"""


def base_comun():
    region = Region.objects.create(name='Biobío', slug='biobio', is_active=True)
    rm = Region.objects.create(name='RM', slug='rm', is_active=True)
    comunas = {}
    for nombre, slug, reg in (('Concepción', 'concepcion', region), ('Maipú', 'maipu', rm),
                              ('Santiago', 'santiago', rm), ('Ñuñoa', 'nunoa', rm), ('Castro', 'castro', rm),
                              ('San Pedro de la Paz', 'san-pedro-de-la-paz', region),
                              ('San Pedro', 'san-pedro', rm)):
        comunas[slug] = Commune.objects.create(region=reg, name=nombre, slug=slug, is_active=True)
    call_command('seed_categorias', stdout=StringIO())
    return comunas


def pdf_con_texto(lineas):
    """Un PDF de verdad, armado a mano (sin librerías), con una línea por Tj."""
    contenido = ['BT', '/F1 10 Tf', '13 TL', '40 800 Td']
    for linea in lineas:
        escapada = linea.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        contenido.append(f'({escapada}) Tj T*')
    contenido.append('ET')
    flujo = '\n'.join(contenido).encode('cp1252')
    objetos = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R '
        b'/Resources << /Font << /F1 5 0 R >> >> >>',
        b'<< /Length %d >>\nstream\n' % len(flujo) + flujo + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
    ]
    salida = bytearray(b'%PDF-1.4\n')
    posiciones = []
    for numero, objeto in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += b'%d 0 obj\n' % numero + objeto + b'\nendobj\n'
    xref = len(salida)
    salida += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objetos) + 1)
    for posicion in posiciones:
        salida += b'%010d 00000 n \n' % posicion
    salida += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objetos) + 1, xref)
    return bytes(salida)


def docx_con_texto(lineas, encabezado=()):
    def xml(parrafos):
        cuerpo = ''.join(f'<w:p><w:r><w:t xml:space="preserve">{p.replace("&", "&amp;").replace("<", "&lt;")}'
                         f'</w:t></w:r></w:p>' for p in parrafos)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f'<w:body>{cuerpo}</w:body></w:document>')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
        paquete.writestr('word/document.xml', xml(lineas))
        if encabezado:
            paquete.writestr('word/header1.xml', xml(encabezado))
    return buffer.getvalue()


def subido(nombre, contenido, tipo='application/pdf'):
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


class LoQueSeProponeEsDeEsaPersona(TestCase):
    def setUp(self):
        self.comunas = base_comun()

    def test_un_cv_de_kinesiologa_llena_el_perfil(self):
        datos = proponer_perfil(CV_KINE)
        self.assertEqual(datos['contact_name'], 'Camila Andrea Rojas Soto')
        self.assertEqual(datos['business_name'], 'Camila Rojas, Kinesióloga')
        self.assertEqual(datos['category'], Category.objects.get(slug='kinesiologia').pk)
        self.assertEqual(datos['profession_title'], 'Kinesióloga')
        self.assertEqual(datos['institution'], 'Universidad de Concepción', 'no el diplomado')
        self.assertEqual(datos['graduation_year'], 2019, 'el año en que terminó, no el de ingreso')
        self.assertEqual(datos['health_registry'], '654321')
        self.assertEqual(datos['commune'], self.comunas['concepcion'].pk)
        self.assertEqual(datos['whatsapp_number'], '+56 9 8765 4321')
        self.assertTrue(datos['attends_home'])
        self.assertTrue(datos['attends_online'])
        self.assertIn('telerehabilitación', datos['description'], 'el corte de línea con guion se une')
        self.assertTrue(datos['short_description'].startswith('Kinesióloga titulada de la Universidad'))
        self.assertLessEqual(len(datos['short_description']), 220)

    def test_lo_privado_del_cv_no_llega_al_perfil(self):
        """El perfil es público: dirección, RUT y correo no se proponen."""
        datos = proponer_perfil(CV_KINE)
        todo = ' '.join(str(v) for v in datos.values())
        for privado in ('Aromos', '18.765.432', 'camila.rojas.kine', '@'):
            self.assertNotIn(privado, todo)
        self.assertNotIn('email', datos)
        self.assertNotIn('address', datos)

    def test_la_comuna_es_donde_vive_no_donde_trabajo_ni_donde_estudio(self):
        """'Dirección de Salud de Maipú' es un empleador; 'Universidad de
        Santiago' es una universidad; un correo con 'santiago' no es domicilio."""
        self.assertEqual(proponer_perfil(CV_KINE)['commune'], self.comunas['concepcion'].pk)
        self.assertEqual(proponer_perfil(CV_GASFITER)['commune'], self.comunas['maipu'].pk)
        self.assertEqual(proponer_perfil(CV_ESTUDIANTE)['commune'], self.comunas['nunoa'].pk)

    def test_un_empleador_no_es_la_comuna(self):
        """Sin dirección en el CV, la comuna se deja en blanco: no se saca del trabajo."""
        datos = proponer_perfil('Pedro Soto Lagos\nKinesiólogo\nExperiencia\n'
                                '2020 – 2023 Kinesiólogo, Dirección de Salud Municipal de Maipú\n')
        self.assertNotIn('commune', datos)

    def test_la_comuna_mas_larga_gana(self):
        datos = proponer_perfil('Andrea Castro Vidal\nComuna: San Pedro de la Paz\n' + 'palabra ' * 20)
        self.assertEqual(datos['commune'], self.comunas['san-pedro-de-la-paz'].pk)

    def test_un_apellido_que_es_comuna_no_es_la_comuna(self):
        datos = proponer_perfil('Andrea Castro Vidal\nNutricionista\n' + 'palabra ' * 20)
        self.assertNotIn('commune', datos)

    def test_un_oficio_tambien_se_reconoce(self):
        datos = proponer_perfil(CV_GASFITER)
        self.assertEqual(datos['category'], Category.objects.get(slug='gasfiteria').pk)
        self.assertEqual(datos['profession_title'], 'Gásfiter')
        self.assertEqual(datos['whatsapp_number'], '+56 9 1234 5678')
        self.assertNotIn('institution', datos, 'un liceo no es "dónde estudiaste" la profesión')

    def test_si_sigue_estudiando_no_se_inventa_el_anio(self):
        datos = proponer_perfil(CV_ESTUDIANTE)
        self.assertEqual(datos['category'], Category.objects.get(slug='psicologia').pk)
        self.assertEqual(datos['institution'], 'Universidad de Santiago de Chile')
        self.assertNotIn('graduation_year', datos)

    def test_la_musica_de_los_pasatiempos_no_es_un_rubro(self):
        datos = proponer_perfil(CV_ESTUDIANTE)
        self.assertNotEqual(datos.get('category'), Category.objects.get(slug='clases-de-musica').pk)
        datos = proponer_perfil(CV_KINE)
        self.assertEqual(datos['category'], Category.objects.get(slug='kinesiologia').pk)

    def test_un_rut_no_pasa_por_celular(self):
        datos = proponer_perfil('Pedro Soto Lagos\nRUT: 9.876.543-2\n' + 'palabra ' * 20)
        self.assertNotIn('whatsapp_number', datos)

    def test_domicilio_como_rotulo_no_es_atencion_a_domicilio(self):
        datos = proponer_perfil('Pedro Soto Lagos\nDomicilio: Av. Siempre Viva 742, Maipú\n' + 'palabra ' * 20)
        self.assertNotIn('attends_home', datos)
        self.assertEqual(datos['commune'], self.comunas['maipu'].pk)

    def test_un_anio_no_es_un_registro(self):
        datos = proponer_perfil('Pedro Soto Lagos\nRegistro: 2019 en curso\n' + 'palabra ' * 20)
        self.assertNotIn('health_registry', datos)

    def test_lo_que_no_esta_claro_se_deja_en_blanco(self):
        self.assertEqual(proponer_perfil('hola ' * 30), {})


class DelArchivoAlTexto(TestCase):

    def test_un_pdf_se_lee(self):
        texto = extraer_texto(subido('cv.pdf', pdf_con_texto(CV_KINE.splitlines())))
        self.assertIn('Kinesióloga', texto)
        self.assertIn('Universidad de Concepción', texto)

    def test_un_word_se_lee_con_su_encabezado(self):
        """Muchas plantillas ponen el nombre y el teléfono en el encabezado."""
        archivo = subido('cv.docx', docx_con_texto(CV_KINE.splitlines()[3:], encabezado=['CAMILA ROJAS SOTO']),
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        texto = extraer_texto(archivo)
        self.assertTrue(texto.startswith('CAMILA ROJAS SOTO'))
        self.assertIn('Universidad de Concepción', texto)

    def test_un_escaneo_se_explica_en_vez_de_llenar_basura(self):
        with self.assertRaisesMessage(CVIlegible, 'foto o un escaneo'):
            extraer_texto(subido('cv.pdf', pdf_con_texto([])))

    def test_una_imagen_no_pasa(self):
        with self.assertRaisesMessage(CVIlegible, 'PDF o en Word'):
            extraer_texto(subido('cv.jpg', b'\xff\xd8\xff\xe0' + b'0' * 500, 'image/jpeg'))

    def test_un_word_antiguo_dice_que_hacer(self):
        with self.assertRaisesMessage(CVIlegible, '.docx'):
            extraer_texto(subido('cv.doc', b'\xd0\xcf\x11\xe0' + b'0' * 500, 'application/msword'))

    def test_un_pdf_roto_no_revienta(self):
        with self.assertRaisesMessage(CVIlegible, 'No pudimos abrir'):
            extraer_texto(subido('cv.pdf', b'%PDF-1.4\nbasura sin objetos'))

    def test_un_zip_que_no_es_word_no_pasa(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as paquete:
            paquete.writestr('otra-cosa.txt', 'hola')
        with self.assertRaisesMessage(CVIlegible, 'PDF o en Word'):
            extraer_texto(subido('cv.docx', buffer.getvalue()))

    def test_mas_de_5_mb_no_se_lee(self):
        with self.assertRaisesMessage(CVIlegible, '5 MB'):
            extraer_texto(subido('cv.pdf', b'%PDF' + b'0' * (5 * 1024 * 1024)))


class ElCVEnElFormulario(TestCase):
    def setUp(self):
        self.comunas = base_comun()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        self.user = User.objects.create_user('camila', email='c@example.cl', password='clave-larga-de-verdad-99')
        self.client.force_login(self.user)

    def leer(self, archivo):
        with override_settings(MEDIA_ROOT=self.media):
            return self.client.post(reverse('accounts:leer_cv'), {'cv': archivo})

    def test_subir_el_cv_llena_el_formulario_y_marca_lo_que_lleno(self):
        respuesta = self.leer(subido('cv.pdf', pdf_con_texto(CV_KINE.splitlines())))
        self.assertRedirects(respuesta, reverse('accounts:provider_create'))
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('value="Camila Rojas, Kinesióloga"', html)
        self.assertIn('value="Universidad de Concepción"', html)
        self.assertIn('value="+56 9 8765 4321"', html)
        self.assertIn('desde-cv', html)
        self.assertIn('Llenamos', html)
        kine = Category.objects.get(slug='kinesiologia')
        self.assertRegex(html, rf'<option value="{kine.pk}" selected>')
        self.assertNotIn('Aromos', html, 'la dirección del CV no se propone')

    def test_el_archivo_no_se_guarda_en_ninguna_parte(self):
        self.leer(subido('cv.pdf', pdf_con_texto(CV_KINE.splitlines())))
        self.assertEqual(list(Path(self.media).rglob('*')), [])
        guardado = self.client.session['cv_borrador']
        self.assertNotIn('Aromos', str(guardado))
        self.assertNotIn('camila.rojas.kine', str(guardado))

    def test_un_cv_ilegible_se_explica_en_el_recuadro(self):
        self.leer(subido('cv.jpg', b'\xff\xd8\xff\xe0' + b'0' * 500, 'image/jpeg'))
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('role="alert"', html)
        self.assertIn('Sube tu CV en PDF o en Word', html)
        self.assertNotIn('cv_borrador', self.client.session)

    def test_publicar_borra_lo_que_quedo_del_cv(self):
        self.leer(subido('cv.pdf', pdf_con_texto(CV_KINE.splitlines())))
        borrador = self.client.session['cv_borrador']
        datos = {k: v for k, v in borrador.items() if not isinstance(v, bool)}
        datos.update({k: 'on' for k, v in borrador.items() if v is True})
        datos.update({'sector': 'Lomas de San Andrés', TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60,
                                                                                     salt='antispam'),
                      HONEYPOT_FIELD: ''})
        respuesta = self.client.post(reverse('accounts:provider_create'), datos)
        self.assertEqual(respuesta.status_code, 302, respuesta.content.decode()[:3000])
        perfil = Provider.objects.get(owner=self.user)
        self.assertEqual(perfil.institution, 'Universidad de Concepción')
        self.assertEqual(perfil.email, '', 'el correo del CV no se publica solo')
        self.assertNotIn('cv_borrador', self.client.session)

    def test_solo_por_post_y_con_cuenta(self):
        self.assertEqual(self.client.get(reverse('accounts:leer_cv')).status_code, 405)
        self.client.logout()
        respuesta = self.client.post(reverse('accounts:leer_cv'), {})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('accounts:login'), respuesta['Location'])


class ElCVAlRegistrarse(TestCase):
    def setUp(self):
        base_comun()

    def registrar(self, **extra):
        datos = {
            'username': 'camila', 'email': 'c@example.cl',
            'password1': 'clave-larga-de-verdad-99', 'password2': 'clave-larga-de-verdad-99',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        }
        datos.update(extra)
        return self.client.post(reverse('accounts:register'), datos)

    def test_el_registro_ofrece_adjuntar_el_cv(self):
        html = self.client.get(reverse('accounts:register')).content.decode()
        self.assertIn('enctype="multipart/form-data"', html)
        self.assertIn('name="cv"', html)

    def test_registrarse_con_cv_deja_el_perfil_llenado(self):
        respuesta = self.registrar(cv=subido('cv.pdf', pdf_con_texto(CV_KINE.splitlines())))
        self.assertRedirects(respuesta, reverse('accounts:provider_create'))
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('value="Universidad de Concepción"', html)

    def test_un_cv_ilegible_no_impide_crear_la_cuenta(self):
        respuesta = self.registrar(cv=subido('cv.jpg', b'\xff\xd8\xff\xe0' + b'0' * 500, 'image/jpeg'))
        # Sin seguir la redirección: el aviso se muestra una sola vez.
        self.assertRedirects(respuesta, reverse('accounts:provider_create'), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username='camila').exists())
        html = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn('Sube tu CV en PDF o en Word', html)

    def test_sin_cv_todo_sigue_igual(self):
        respuesta = self.registrar()
        self.assertRedirects(respuesta, reverse('accounts:provider_create'))
        self.assertNotIn('cv_borrador', self.client.session)


class RubrosNuevosEnElCV(TestCase):
    def setUp(self):
        base_comun()

    def test_un_desarrollador_queda_en_desarrollo_web_no_en_soporte(self):
        datos = proponer_perfil('Diego Pérez Soto\nIngeniero en Informática\nPerfil\n'
                                'Desarrollador full stack con experiencia en sitios web y sistemas a medida.\n')
        self.assertEqual(datos['category'], Category.objects.get(slug='desarrollo-web').pk)

    def test_un_tecnico_en_computacion_sigue_en_soporte(self):
        datos = proponer_perfil('Pedro Soto Lagos\nTécnico en computación\nFormateo y redes para hogares.\n')
        self.assertEqual(datos['category'], Category.objects.get(slug='soporte-computacional').pk)
