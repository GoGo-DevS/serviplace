"""Leer un CV y proponer con él los datos del perfil (18-10-2026).

Pedido de Diego: "que al registrarse les dé la opción de adjuntar CV, y ojalá
que el CV llene los datos del formulario". Quien recién se titula ya tiene su
CV hecho; copiarlo campo por campo es justo el paso donde se abandona.

Reglas (Ley 21.719, memoria ley-21719-blindar-gogodevs):
- El archivo NO se guarda: se lee en memoria durante la petición y se suelta.
- Se lee aquí mismo, sin IA: el CV no viaja a ningún tercero ni gasta cuota.
- Solo se proponen campos del formulario. La dirección, el RUT, el correo, la
  fecha de nacimiento y el estado civil que trae todo CV chileno NO se copian:
  el perfil es público y eso no tiene por qué quedar a la vista.
- Nada se publica solo: la persona revisa el formulario y aprieta Publicar.

Es una lectura por reglas, no adivinación: si un dato no está claro se deja en
blanco. Un campo vacío se llena en diez segundos; uno mal llenado se publica.
"""
import html
import re
import unicodedata
import zipfile

from django.utils import timezone

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGINAS = 6            # un CV largo tiene tres; más que eso no es un CV
MAX_XML = 8 * 1024 * 1024  # tope al descomprimir un Word (bomba zip)
MAX_TEXTO = 30_000

ACEPTA = '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'


class CVIlegible(Exception):
    """El archivo no se pudo leer. El mensaje se le muestra tal cual a la persona."""


# --------------------------------------------------------------------------
# 1. Del archivo al texto
# --------------------------------------------------------------------------

def extraer_texto(archivo):
    if archivo.size > MAX_BYTES:
        raise CVIlegible('Tu CV pesa más de 5 MB. Expórtalo de nuevo en PDF o súbelo en Word (.docx).')
    archivo.seek(0)
    cabecera = archivo.read(1024)
    archivo.seek(0)
    if b'%PDF' in cabecera:
        texto = _texto_pdf(archivo)
    elif cabecera.startswith(b'PK'):
        texto = _texto_docx(archivo)
    elif cabecera.startswith(b'\xd0\xcf\x11\xe0'):
        raise CVIlegible('Ese es un Word antiguo (.doc). Guárdalo como .docx o PDF y vuelve a subirlo.')
    else:
        raise CVIlegible('Sube tu CV en PDF o en Word (.docx).')
    texto = texto.replace('\x00', '').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    if len(re.findall(r'[^\W\d_]{2,}', texto)) < 15:
        raise CVIlegible(
            'No encontramos texto en tu CV: parece una foto o un escaneo. Sube el PDF que '
            'exporta Word o Canva, o llena el formulario a mano.'
        )
    return texto[:MAX_TEXTO]


# Los PDF hechos con LaTeX guardan la tilde como un signo APARTE y ANTES de la
# vocal: "Inform´atico", "Espa˜na", "ling¨u´ıstica" (con ı sin punto). Al
# extraer el texto, esa tilde termina suelta o pegada a la letra anterior, y el
# 20-10-2026 un perfil quedó publicado como "Ingeniero Inforḿatico".
_ANTES_DE_LA_LETRA = {'\u00b4': '\u0301', '\u02ca': '\u0301', '\u02dc': '\u0303', '\u00a8': '\u0308'}
_VOCAL = 'aeiouAEIOU'


def reparar_tildes(texto):
    """Devuelve cada tilde a su letra. En español una consonante nunca lleva
    tilde aguda, ni una vocal virgulilla, ni la g diéresis: si aparecen, la
    marca era de la letra siguiente."""
    if not texto:
        return texto
    # 1) Signo suelto antes de la letra: "´a" -> "á", "˜n" -> "ñ", "¨u" -> "ü".
    texto = re.sub(r'([\u00b4\u02ca])\s?([aeiouıAEIOU])',
                   lambda m: ('i' if m.group(2) == 'ı' else m.group(2)) + '\u0301', texto)
    texto = re.sub(r'\u02dc\s?([nN])', lambda m: m.group(1) + '\u0303', texto)
    texto = re.sub(r'\u00a8\s?([uU])', lambda m: m.group(1) + '\u0308', texto)
    # 2) La marca quedó en la letra anterior: se pasa a la siguiente.
    texto = unicodedata.normalize('NFD', texto)
    texto = re.sub(r'([^\W\d_aeiouAEIOU])\u0301([aeiouıAEIOU])',
                   lambda m: m.group(1) + ('i' if m.group(2) == 'ı' else m.group(2)) + '\u0301', texto)
    texto = re.sub(r'([aeiouAEIOU])\u0303([nN])', lambda m: m.group(1) + m.group(2) + '\u0303', texto)
    texto = re.sub(r'([gG])\u0308([uU])', lambda m: m.group(1) + m.group(2) + '\u0308', texto)
    texto = texto.replace('ı\u0301', 'i\u0301')
    return unicodedata.normalize('NFC', texto)


def _texto_pdf(archivo):
    from pypdf import PdfReader
    try:
        lector = PdfReader(archivo)
        if lector.is_encrypted and not lector.decrypt(''):
            raise CVIlegible('Tu PDF tiene contraseña. Expórtalo sin contraseña o súbelo en Word (.docx).')
        return '\n'.join((pagina.extract_text() or '') for pagina in lector.pages[:MAX_PAGINAS])
    except CVIlegible:
        raise
    except Exception:  # pypdf lanza de todo ante un PDF dañado
        raise CVIlegible('No pudimos abrir ese PDF. Expórtalo de nuevo o súbelo en Word (.docx).')


def _texto_docx(archivo):
    """Sin python-docx: el texto de un .docx está en word/document.xml, y el
    nombre y el teléfono muchas veces en el encabezado (word/header*.xml)."""
    try:
        with zipfile.ZipFile(archivo) as paquete:
            nombres = sorted(n for n in paquete.namelist() if re.fullmatch(r'word/header\d*\.xml', n))
            partes = []
            for nombre in nombres + ['word/document.xml']:
                with paquete.open(nombre) as parte:
                    xml = parte.read(MAX_XML + 1)
                if len(xml) > MAX_XML:
                    raise CVIlegible('No pudimos leer ese Word. Expórtalo en PDF y vuelve a subirlo.')
                partes.append(xml.decode('utf-8', 'ignore'))
    except CVIlegible:
        raise
    except Exception:  # no es un .docx (KeyError), zip dañado o cifrado
        raise CVIlegible('Sube tu CV en PDF o en Word (.docx).')
    xml = '\n'.join(partes)
    xml = re.sub(r'<w:tab\b[^>]*/>', ' ', xml)
    xml = re.sub(r'</w:p>|<w:br\b[^>]*/>|<w:cr\b[^>]*/>', '\n', xml)
    return html.unescape(re.sub(r'<[^>]+>', '', xml))


# --------------------------------------------------------------------------
# 2. Del texto a los campos del formulario
# --------------------------------------------------------------------------

def _plano(texto):
    """Minúsculas y sin tildes, CON EL MISMO LARGO que el original: así una
    coincidencia en el texto plano se recorta del original con sus tildes."""
    salida = []
    for c in texto:
        base = ''.join(b for b in unicodedata.normalize('NFKD', c) if not unicodedata.combining(b))
        base = base if len(base) == 1 else c
        minuscula = base.lower()
        salida.append(minuscula if len(minuscula) == 1 else base)
    return ''.join(salida)


def _oracion(texto):
    """'KINESIÓLOGA' o 'kinesióloga' -> 'Kinesióloga'. Lo que ya viene con
    mayúsculas y minúsculas se respeta."""
    texto = ' '.join(texto.split()).strip(' .,;:-–|•')
    if not texto:
        return ''
    if texto.isupper() or texto.islower():
        texto = texto.lower()
    return texto[0].upper() + texto[1:]


SIGLAS = {'inacap', 'duoc', 'uc', 'aiep', 'cft', 'ip', 'utfsm', 'usach', 'ucsc', 'ufro', 'tens'}
PARTICULAS = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'en', 'van', 'von', 'da', 'di'}


def _nombre_propio(texto):
    """'CAMILA ROJAS DE LA FUENTE' -> 'Camila Rojas de la Fuente'."""
    texto = ' '.join(texto.split()).strip(' .,;:-–|•')
    if not (texto.isupper() or texto.islower()):
        return texto
    palabras = []
    for i, palabra in enumerate(texto.lower().split()):
        if _plano(palabra) in SIGLAS:
            palabras.append(palabra.upper())
        elif i and palabra in PARTICULAS:
            palabras.append(palabra)
        else:
            palabras.append('-'.join(p[:1].upper() + p[1:] for p in palabra.split('-')))
    return ' '.join(palabras)


# Títulos de sección, ya en texto plano.
SEC_PERFIL = {'perfil', 'perfil profesional', 'perfil laboral', 'resumen', 'resumen profesional', 'sobre mi',
              'acerca de mi', 'presentacion', 'extracto', 'quien soy'}
SEC_FORMACION = {'formacion', 'formacion academica', 'formacion profesional', 'educacion', 'estudios',
                 'antecedentes academicos', 'estudios superiores', 'titulos', 'educacion superior',
                 'antecedentes educacionales', 'formacion educacional'}
SEC_EXPERIENCIA = {'experiencia', 'experiencia laboral', 'experiencia profesional', 'antecedentes laborales',
                   'practicas', 'practicas profesionales', 'experiencia clinica', 'trayectoria'}
SEC_OTRAS = {'habilidades', 'competencias', 'idiomas', 'cursos', 'certificaciones', 'referencias', 'contacto',
             'datos personales', 'informacion personal', 'informacion de contacto', 'objetivo',
             'objetivo profesional', 'objetivo laboral', 'conocimientos', 'herramientas', 'logros', 'intereses',
             'voluntariado', 'publicaciones', 'capacitaciones', 'capacitacion', 'perfeccionamiento', 'diplomados',
             'postitulos', 'aptitudes', 'software', 'disponibilidad', 'pretension de renta', 'otros antecedentes',
             'antecedentes personales', 'cursos y certificaciones', 'cursos y capacitaciones', 'habilidades blandas',
             'conocimientos tecnicos', 'otros', 'pasatiempos', 'premios', 'actividades extracurriculares'}
SECCIONES = ({t: 'perfil' for t in SEC_PERFIL} | {t: 'formacion' for t in SEC_FORMACION}
             | {t: 'experiencia' for t in SEC_EXPERIENCIA} | {t: 'otra' for t in SEC_OTRAS})

INSTITUCION = re.compile(
    r'\b(?:pontificia universidad|universidad|instituto profesional|instituto|centro de formacion tecnica|'
    r'cft|ip|inacap|duoc(?: uc)?|aiep|santo tomas|conservatorio|escuela de (?:enfermeria|obstetricia|salud))\b'
)
POSGRADO = re.compile(r'diplomado|magister|master|postitulo|postgrado|posgrado|doctorado|\bcurso\b|seminario|'
                      r'congreso|capacitacion|especializacion|certificacion')
# Con dos puntos: "Dirección de Salud de Maipú" es un empleador, no un domicilio.
DIRECCION = re.compile(r'\b(?:direccion|domicilio|comuna|residencia|ubicacion|ciudad)\s*:|\bvivo en\b|\breside en\b')
CORREO_O_WEB = re.compile(r'\S+@\S+|\S*(?:https?://|www\.|\.com|\.cl)\S*')
ANIO = re.compile(r'\b(19[5-9]\d|20[0-4]\d)\b')
EN_CURSO = re.compile(r'actualidad|presente|en curso|cursando|a la fecha|\bhoy\b|actual\b')

# (rubro, quien lo ejerce, la disciplina). Se buscan en este orden y lo que
# calza se tacha: "profesor de inglés" es de idiomas y ya no cuenta como
# "profesor" para clases particulares.
PROFESIONES = [
    ('psicopedagogia', r'psicopedagog[oa]s?|educador[a]? diferencial|profesor[a]? de educacion diferencial',
     r'psicopedagogia|educacion diferencial'),
    ('kinesiologia', r'kinesiolog[oa]s?', r'kinesiologia'),
    ('psicologia', r'psicolog[oa]s?', r'psicologia'),
    ('nutricion', r'nutricionista', r'nutricion y dietetica|nutricion'),
    ('fonoaudiologia', r'fonoaudiolog[oa]s?', r'fonoaudiologia'),
    ('terapia-ocupacional', r'terapeuta ocupacional', r'terapia ocupacional'),
    ('enfermeria', r'tecnic[oa] en enfermeria(?: de nivel superior)?|tens|enfermer[oa]', r'enfermeria'),
    ('podologia', r'podolog[oa]s?', r'podologia'),
    ('cuidado-de-personas', r'cuidador[a]?|asistente de adultos? mayor(?:es)?', r'cuidado de adultos? mayor(?:es)?'),
    ('idiomas', r'profesor[a]? de (?:ingles|frances|aleman|portugues|italiano|idiomas)|traductor[a]?|'
                r'interprete(?! musical)', r'pedagogia en ingles|traduccion e interpretacion'),
    ('clases-de-musica', r'profesor[a]? de (?:musica|guitarra|piano|canto|violin)|interprete musical',
     r'pedagogia en (?:educacion )?musica|interpretacion musical'),
    ('clases-particulares', r'profesor[a]? de (?:matematicas?|lenguaje|historia|ciencias|fisica|quimica|biologia|'
                            r'educacion (?:general )?basica|educacion media)|educador[a]? de parvulos|profesor[a]?',
     r'pedagogia en [a-z]+|educacion de parvulos|pedagogia'),
    ('peluqueria', r'peluquer[oa]|estilista|barber[oa]?', r'peluqueria|barberia'),
    ('manicure-y-estetica', r'manicurista|cosmetolog[oa]|esteticista|tecnic[oa] en estetica|lashista',
     r'cosmetologia|estetica integral|manicure'),
    ('contabilidad', r'contador[a]?(?: auditor[a]?| public[oa])?|ingenier[oa] en contabilidad|'
                     r'tecnic[oa] en contabilidad', r'contabilidad|auditoria'),
    ('diseno-grafico', r'disenador[a]? grafic[oa]', r'diseno grafico'),
    ('fotografia-y-video', r'fotograf[oa]|realizador[a]? audiovisual|camarograf[oa]',
     r'fotografia|comunicacion audiovisual'),
    # 18-10-2026: rubros nuevos. Desarrollo va ANTES que soporte: "ingeniero en
    # informática" y "desarrollador full stack" en el mismo CV es desarrollo.
    ('desarrollo-web', r'desarrollador[a]? (?:web|full ?stack|front ?end|back ?end|de software|de aplicaciones)|'
                       r'programador[a]?|ingenier[oa] de software|analista programador[a]?',
     r'desarrollo web|desarrollo de software|desarrollo de aplicaciones'),
    ('tatuajes', r'tatuador[a]?|tatuajista|perforador[a]?', r'tatuajes?|piercing'),
    ('seguridad-hogar', r'instalador[a]? de (?:alarmas|camaras|cctv|sistemas de seguridad)', r'cctv|sistemas de seguridad'),
    ('fletes-y-logistica', r'fletero|conductor[a]? de camion|camioner[oa]|operador[a]? logistic[oa]',
     r'fletes|mudanzas|logistica'),
    ('traslados-y-turismo', r'conductor[a]? (?:de )?(?:transporte de pasajeros|turismo|van|minibus)|chofer de turismo',
     r'transporte de pasajeros|traslados al aeropuerto'),
    ('soporte-computacional', r'tecnic[oa] (?:en )?(?:informatica|computacion|redes|soporte)|analista programador[a]?|'
                              r'ingenier[oa] (?:de ejecucion )?(?:en )?(?:informatica|computacion)',
     r'soporte tecnico|soporte computacional'),
    ('gasfiteria', r'gasfiter|instalador[a]? sanitari[oa]|instalador[a]? de gas', r'gasfiteria'),
    ('electricidad', r'electricista|tecnic[oa] (?:en )?(?:electricidad|electric[oa])|instalador[a]? electric[oa]',
     r'electricidad'),
    ('climatizacion', r'tecnic[oa] (?:en )?(?:climatizacion|refrigeracion)|frigorista', r'climatizacion|refrigeracion'),
    ('construccion', r'maestro (?:constructor|mayor|de obras?|albanil)|albanil|constructor[a]? civil',
     r'construccion civil'),
    ('carpinteria', r'carpinter[oa]|mueblista', r'carpinteria|muebleria'),
    ('soldadura', r'soldador[a]?|maestro soldador|estructurer[oa]', r'soldadura|estructuras metalicas'),
    ('pintura', r'pintor[a]?', r'pintura'),
    ('jardineria', r'jardiner[oa]|paisajista', r'jardineria|paisajismo'),
    ('limpieza', r'auxiliar de aseo|asesora del hogar|personal de aseo', r'servicio de aseo'),
    ('cerrajeria', r'cerrajer[oa]', r'cerrajeria'),
]
PROFESIONES = [(slug, re.compile(rf'\b(?:{quien})\b'), re.compile(rf'\b(?:{area})\b'))
               for slug, quien, area in PROFESIONES]


class _Linea:
    __slots__ = ('i', 'texto', 'plana', 'seccion')

    def __init__(self, i, texto, seccion):
        self.i, self.texto, self.plana, self.seccion = i, texto, _plano(texto), seccion


def _lineas(texto):
    """Cada línea con la sección del CV a la que pertenece. Un título con
    contenido en la misma línea ("Perfil: kinesióloga con...") abre la sección
    y deja el contenido como primera línea."""
    lineas, seccion, vio_titulo = [], 'cabecera', False
    for cruda in texto.splitlines():
        linea = re.sub(r'^[\s•●▪■◦○\-–—*·>]+', '', ' '.join(cruda.split()))
        plana = _plano(linea).strip(' :.-–—|')
        if plana in SECCIONES:
            seccion, vio_titulo = SECCIONES[plana], True
            continue
        cabeza, dos_puntos, resto = linea.partition(':')
        if dos_puntos and _plano(cabeza).strip() in SECCIONES and resto.strip():
            seccion, vio_titulo = SECCIONES[_plano(cabeza).strip()], True
            linea = resto.strip()
        elif (seccion == 'perfil' and linea.isupper() and len(linea.split()) <= 5 and len(linea) > 3
              and not ANIO.search(linea) and not INSTITUCION.search(plana)):
            # Un título que no está en la lista ("CURSOS Y TALLERES") no puede
            # quedar pegado a la descripción: cierra el perfil.
            seccion = 'otra'
        lineas.append(_Linea(len(lineas), linea, seccion))
    return lineas


def _nombre(lineas):
    for l in lineas[:40]:
        m = re.match(r'nombre(?: completo)?\s*[:\-–]\s*(.+)$', l.plana)
        if m:
            return _nombre_propio(l.texto[m.start(1):])[:120], l.i
    vistas = 0
    for l in lineas:
        if not l.texto:
            continue
        vistas += 1
        if vistas > 8 or l.seccion in ('perfil', 'formacion', 'experiencia'):
            break
        palabras = l.texto.split()
        if (2 <= len(palabras) <= 6 and len(l.texto) <= 60
                and all(re.fullmatch(r"[^\W\d_]+(?:['’.-][^\W\d_]+)*\.?", p) for p in palabras)
                and any(p[0].isupper() for p in palabras)
                and not re.search(r'curriculum|curriculo|vitae|\bcv\b|hoja de vida|perfil|datos|contacto|'
                                  r'resumen|direccion|telefono|correo|email|celular|chile\b|region', l.plana)
                and not INSTITUCION.search(l.plana)
                and not any(quien.search(l.plana) or area.search(l.plana) for _, quien, area in PROFESIONES)):
            return _nombre_propio(l.texto)[:120], l.i
    return '', None


def _puntajes(lineas):
    """Puntos por rubro (lo de la cabecera vale más) y cómo se nombra la persona."""
    planas = [list(l.plana) for l in lineas]
    puntos, primera = {}, {}
    for slug, quien, area in PROFESIONES:
        for patron, peso in ((quien, 3), (area, 1)):
            for l in lineas:
                texto = ''.join(planas[l.i])
                for m in patron.finditer(texto):
                    extra = 2 if l.seccion in ('cabecera', 'perfil') else 0
                    puntos[slug] = puntos.get(slug, 0) + peso + extra
                    if peso == 3 and slug not in primera:
                        primera[slug] = l.texto[m.start():m.end()]
                    planas[l.i][m.start():m.end()] = ' ' * (m.end() - m.start())
    return puntos, primera


def _profesion(lineas):
    """El rubro que más aparece (lo de la cabecera vale más) y cómo se nombra
    la persona: 'Kinesióloga' sale de 'kinesiólog[oa]', no de 'kinesiología'."""
    puntos, primera = _puntajes(lineas)
    if not puntos:
        return None, ''
    orden = list(puntos)  # a igual puntaje gana el que va primero en PROFESIONES
    slug = max(puntos, key=lambda s: (puntos[s], -orden.index(s)))
    if puntos[slug] < 2:
        return None, ''
    titulo = primera.get(slug, '')
    return slug, ('TENS' if _plano(titulo) == 'tens' else _oracion(titulo))


def _otras_profesiones(lineas, principal, tope=5):
    """Los demás oficios que la persona se atribuye ("maestro constructor,
    gásfiter, electricista"): al menos una mención como oficio (3 puntos), no
    una palabra suelta en la experiencia."""
    puntos, _ = _puntajes(lineas)
    orden = list(puntos)
    candidatos = sorted((s for s in puntos if s != principal and puntos[s] >= 3),
                        key=lambda s: (-puntos[s], orden.index(s)))
    return candidatos[:tope]


def _titulo_explicito(lineas):
    for l in lineas:
        m = re.match(r'(?:titulo(?: profesional)?|profesion|ocupacion)\s*[:\-–]\s*(.+)$', l.plana)
        if m:
            texto = l.texto[m.start(1):]
            texto = re.split(r'\s[-–|]\s|,|;|\(|\s(?:19|20)\d{2}\b', texto)[0]
            return _oracion(texto)[:120]
    return ''


def _institucion(lineas, slug):
    patrones = [p for s, q, a in PROFESIONES if s == slug for p in (q, a)]
    mejor, mejor_puntos = None, None
    for l in lineas:
        m = INSTITUCION.search(l.plana)
        if not m:
            continue
        vecinas = ' '.join(x.plana for x in lineas[max(0, l.i - 1):l.i + 2])
        puntos = 3 if l.seccion == 'formacion' else 0
        puntos -= 2 if l.seccion == 'experiencia' else 0
        puntos += 2 if any(p.search(vecinas) for p in patrones) else 0
        puntos += 1 if re.search(r'titul|licenciad|carrera|pregrado|egresad', vecinas) else 0
        puntos -= 3 if POSGRADO.search(l.plana) else 0
        if puntos >= 0 and (mejor_puntos is None or puntos > mejor_puntos):
            mejor, mejor_puntos = (l, m.start()), puntos
    if not mejor:
        return '', None
    l, inicio = mejor
    nombre = re.split(r'\s+[-–—|•·]\s+|,|;|\(|\s(?:19|20)\d{2}\b|\s{2,}|\.\s', l.texto[inicio:])[0]
    return _nombre_propio(nombre)[:140], l


def _anio_titulacion(lineas, linea):
    """El año más alto junto a la institución ("2014 – 2019" -> 2019). Si la
    carrera sigue en curso no se adivina: se deja en blanco."""
    if linea is None:
        return None
    tope = timezone.localdate().year + 7
    seccion = [x for x in lineas if x.seccion == linea.seccion and x.texto]
    k = seccion.index(linea)
    # Si la sección parte con los años ("2014 – 2019 / Kinesiología / U. de
    # Concepción"), el año de una entrada está ARRIBA y el de abajo ya es de
    # la entrada siguiente. Si parte con la carrera, es al revés.
    anio_arriba = bool(ANIO.search(seccion[0].plana)) and not INSTITUCION.search(seccion[0].plana)
    orden = (k, k - 1, k - 2, k + 1, k + 2) if anio_arriba else (k, k + 1, k + 2, k - 1, k - 2)
    for j in orden:
        if not 0 <= j < len(seccion) or (j != k and INSTITUCION.search(seccion[j].plana)):
            continue  # fuera de la sección, o ya es otra entrada (otro título, otro año)
        anios = [int(a) for a in ANIO.findall(seccion[j].plana) if int(a) <= tope]
        if anios:
            if EN_CURSO.search(seccion[j].plana) and max(anios) <= timezone.localdate().year:
                return None
            return max(anios)
    return None


def _registro_salud(texto_plano):
    m = re.search(
        r'(?:\brnpi\b|superintendencia de salud|registro nacional de prestadores[a-z ]*|'
        r'\bn[°º.o]?\s*(?:de\s+)?registro|registro\s*(?:sis\s*)?(?:n[°º.o]\.?\s*|:))'
        r'[^\d\n]{0,40}?(\d[\d.]{2,12})',
        texto_plano,
    )
    if not m:
        return ''
    digitos = m.group(1).replace('.', '')
    if len(digitos) == 4 and 1950 <= int(digitos) <= 2040:
        return ''  # es un año, no un registro
    return digitos if 3 <= len(digitos) <= 10 else ''


def _celular(texto):
    # Solo el celular: es el WhatsApp del perfil. El patrón exige 9 + 8
    # dígitos sin un dígito pegado antes, así un RUT no pasa por teléfono.
    from accounts.forms import formatear_telefono, normalizar_movil
    m = re.search(r'(?<![\d.])(?:\+?\s?56[\s.-]*)?\(?9\)?[\s.-]*\d{4}[\s.-]*\d{4}(?![\d.-]?\d)', texto)
    return formatear_telefono(normalizar_movil(m.group())) if m and normalizar_movil(m.group()) else ''


def _comuna(lineas, linea_nombre):
    """Solo donde el CV dice dónde vive la persona: una línea de dirección o
    la cabecera. 'Universidad de Concepción' no dice que viva en Concepción,
    y 'Castro' o 'Molina' en el nombre tampoco."""
    from directory.models import Commune
    candidatas = [l for l in lineas if DIRECCION.search(l.plana)]
    candidatas += [l for l in lineas[:12] if l.seccion == 'cabecera' and l.i != linea_nombre]
    candidatas = [l for l in candidatas if not INSTITUCION.search(l.plana)]
    if not candidatas:
        return None
    # La más larga primero: "San Pedro de la Paz" antes que "San Pedro".
    comunas = sorted(((_plano(nombre), pk) for pk, nombre in
                      Commune.objects.filter(is_active=True).values_list('pk', 'name')),
                     key=lambda c: -len(c[0]))
    for l in candidatas:
        texto = CORREO_O_WEB.sub(' ', l.plana)  # camila.maipu@gmail.com no dice dónde vive
        for nombre, pk in comunas:
            if re.search(rf'(?<!\w){re.escape(nombre)}(?!\w)', texto):
                return pk
    return None


def _perfil(lineas):
    parrafos, actual = [], []
    for l in lineas:
        if l.seccion != 'perfil':
            continue
        if not l.texto:
            if actual:
                parrafos.append(' '.join(actual))
                actual = []
            continue
        actual.append(l.texto)
    if actual:
        parrafos.append(' '.join(actual))
    texto = '\n\n'.join(parrafos).strip()
    texto = re.sub(r'([a-záéíóúñ])- ([a-záéíóúñ])', r'\1\2', texto)  # "rehabili- tación" del corte de línea
    if len(texto) > 1200:
        corte = texto.rfind('.', 0, 1200)
        texto = texto[:corte + 1] if corte > 200 else texto[:1200].rsplit(' ', 1)[0] + '…'
    return texto


def proponer_perfil(texto):
    """Devuelve {campo del ProviderForm: valor} solo con lo que se encontró.

    Los valores son de tipos que la sesión puede guardar (JSON): rubro y
    comuna van como pk.
    """
    from directory.models import Category

    texto = reparar_tildes(texto)  # aquí y no al extraer: todo texto de CV pasa por esta puerta
    lineas = _lineas(texto)
    # Para buscar palabras sueltas se unen las cortadas con guion al final de
    # una línea ("telerehabilita-\nción"). Este texto no se recorta: el largo
    # puede cambiar.
    plano = _plano(re.sub(r'([^\W\d_])-[ \t]*\n\s*([^\W\d_])', r'\1\2', texto))
    datos = {}

    nombre, linea_nombre = _nombre(lineas)
    slug, titulo = _profesion(lineas)
    titulo = _titulo_explicito(lineas) or titulo
    categoria = Category.objects.filter(slug=slug, is_active=True).first() if slug else None
    institucion, linea_institucion = _institucion(lineas, slug)
    movil = _celular(texto)

    if nombre:
        datos['contact_name'] = nombre
        palabras = [p for p in nombre.split() if p.lower() not in PARTICULAS]
        # "Camila Andrea Rojas Soto" -> "Camila Rojas"; con tres palabras se
        # asume nombre + dos apellidos. Es una sugerencia: se edita.
        corto = ' '.join(palabras[:1] + [palabras[2] if len(palabras) >= 4 else palabras[1]])
        datos['business_name'] = f'{corto}, {titulo}'[:140] if titulo else nombre
    if categoria:
        datos['category'] = categoria.pk
        otros = _otras_profesiones(lineas, slug)
        pks = dict(Category.objects.filter(slug__in=otros, is_active=True).values_list('slug', 'pk'))
        if pks:
            datos['otras_categorias'] = [pks[s] for s in otros if s in pks]
    if titulo:
        datos['profession_title'] = titulo
    if institucion:
        datos['institution'] = institucion
        anio = _anio_titulacion(lineas, linea_institucion)
        if anio:
            datos['graduation_year'] = anio
    registro = _registro_salud(plano)
    if registro:
        datos['health_registry'] = registro
    comuna = _comuna(lineas, linea_nombre)
    if comuna:
        datos['commune'] = comuna
    if movil:
        datos['whatsapp_number'] = movil
        datos['phone'] = movil

    descripcion = _perfil(lineas)
    if descripcion:
        datos['description'] = descripcion
        primera = re.split(r'(?<=[.!?])\s+', descripcion.replace('\n', ' '))[0].strip()
        if 25 <= len(primera) <= 220:
            datos['short_description'] = primera
    if 'short_description' not in datos and titulo:
        datos['short_description'] = f'{titulo} · {institucion}'[:220] if institucion else titulo

    if re.search(r'a domicilio|atencion domiciliaria|visitas domiciliarias|domiciliari[oa]s?\b', plano):
        datos['attends_home'] = True
    if re.search(r'\bonline\b|telemedicina|teleconsulta|telerehabilitacion|telesalud|videollamada|'
                 r'atencion remota|clases remotas|\ben linea\b', plano):
        datos['attends_online'] = True
    if re.search(r'consulta particular|consulta privada|consulta propia|box de atencion', plano):
        datos['attends_office'] = True
    return datos
