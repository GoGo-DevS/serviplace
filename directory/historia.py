"""Historia de Instagram con la ficha de un profesional (02-11-2026).

Diego: "una ficha para compartir fácil en IG como storie, y que eso se
pegue". Cada historia que sube un profesional lleva la marca y el enlace de
ServiPlace a sus seguidores, que son sus clientes y muchas veces otros
independientes: es la forma más barata de que ServiPlace se conozca.

Se dibuja con Pillow en el servidor (sin navegador ni servicios de afuera),
1080x1920, con las fuentes del sitio (directory/fuentes/). Lo importante
queda entre y=250 y y=1700: arriba Instagram pone el nombre de la cuenta y
abajo la barra para responder. Sin emojis ni flechas (voz de marca) y sin
teléfono: el enlace lleva a la ficha, que ya lo muestra.
"""
import io
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

# Subirlo cuando cambie el dibujo: cambia la versión de todas las historias
# (Provider.version_historia) y nadie recibe la imagen vieja guardada.
DISENO = 1

ANCHO, ALTO = 1080, 1920
FUENTES = Path(__file__).resolve().parent / 'fuentes'
TITULO = 'bricolage-grotesque.ttf'      # variable: por defecto viene en peso 800
TEXTO = 'atkinson-hyperlegible-400.ttf'
NEGRITA = 'atkinson-hyperlegible-700.ttf'

FONDO, CUADRICULA = '#1b1f24', '#2a3038'
TINTA, GRIS, ACENTO, MARCA, VERDE = '#1b1f24', '#5a6068', '#0e7490', '#06b6d4', '#0f7a40'
CHIPS = {  # fondo, letra: los mismos tonos de las insignias del sitio
    'verificado': ('#fbf0d6', '#8a5a00'),
    'sello': ('#dcefe2', '#0b6233'),
    'rubro': ('#cffafe', '#155e75'),
    'modalidad': ('#eef2f6', '#3a4047'),
}

# Zona donde cabe la tarjeta, entre la marca de arriba y el enlace de abajo.
TARJETA_X, TARJETA_ANCHO = 80, 920
ZONA_ARRIBA, ZONA_ABAJO = 420, 1490
RELLENO = 56

# Fuera del alfabeto latino (emojis, símbolos) las fuentes no tienen el
# dibujo y saldría un cuadrado vacío: se quita.
_FUERA_DE_LA_FUENTE = re.compile('[^ -ɏ–—‘’“”…]')


@lru_cache(maxsize=None)
def _fuente(nombre, tamano):
    try:
        return ImageFont.truetype(str(FUENTES / nombre), tamano)
    except OSError:  # sin el archivo la historia sale igual, con la fuente de Pillow
        return ImageFont.load_default(size=tamano)


def _limpio(texto):
    return ' '.join(_FUERA_DE_LA_FUENTE.sub('', texto or '').split())


def _partir(texto, fuente, ancho, max_lineas):
    """Corta el texto en líneas que caben en `ancho`; si sobra, la última
    termina en puntos suspensivos."""
    lineas, actual = [], ''
    for palabra in texto.split():
        prueba = f'{actual} {palabra}'.strip()
        if fuente.getlength(prueba) <= ancho:
            actual = prueba
            continue
        if actual:
            lineas.append(actual)
        actual = palabra
        while fuente.getlength(actual) > ancho and len(actual) > 1:  # una palabra más ancha que la línea
            corte = len(actual) - 1
            while corte > 1 and fuente.getlength(actual[:corte]) > ancho:
                corte -= 1
            lineas.append(actual[:corte])
            actual = actual[corte:]
    if actual:
        lineas.append(actual)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        ultima = lineas[-1]
        while ultima and fuente.getlength(ultima + '…') > ancho:
            ultima = ultima[:-1].rstrip()
        lineas[-1] = ultima + '…'
    return lineas


def _mascara(ancho, alto, radio=0, elipse=False):
    """Forma dibujada al doble y achicada: bordes suaves, sin serrucho. BOX y
    no LANCZOS: para promediar píxeles basta, y la tarjeta entera es grande."""
    grande = Image.new('L', (ancho * 2, alto * 2), 0)
    lapiz = ImageDraw.Draw(grande)
    caja = (0, 0, ancho * 2 - 1, alto * 2 - 1)
    if elipse:
        lapiz.ellipse(caja, fill=255)
    else:
        lapiz.rounded_rectangle(caja, radius=radio * 2, fill=255)
    return grande.resize((ancho, alto), Image.BOX)


def _forma(img, x, y, ancho, alto, color, radio=0, elipse=False):
    ancho, alto = int(ancho), int(alto)
    img.paste(Image.new('RGB', (ancho, alto), color), (int(x), int(y)), _mascara(ancho, alto, radio, elipse))


def _pegar_foto(img, foto, x, y, ancho, alto, radio=0, elipse=False):
    ancho, alto = int(ancho), int(alto)
    recorte = ImageOps.fit(foto, (ancho, alto), Image.BICUBIC)
    img.paste(recorte, (int(x), int(y)), _mascara(ancho, alto, radio, elipse))


def _abrir(campo):
    """La foto guardada (en R2 en producción), o None si no se puede leer:
    un archivo perdido no puede dejar al profesional sin su historia."""
    try:
        with campo.open('rb') as archivo:
            imagen = Image.open(archivo)
            imagen.load()
        return imagen.convert('RGB')
    except Exception:
        return None


@lru_cache(maxsize=4)
def _logo(lado):
    """El pin de ServiPlace (static/img/marca), redibujado desde su SVG de 64x64."""
    e = lado * 8 / 64
    capa = Image.new('RGBA', (lado * 8, lado * 8), (0, 0, 0, 0))
    lapiz = ImageDraw.Draw(capa)
    puntos = lambda pares: [(x * e, y * e) for x, y in pares]
    lapiz.ellipse((9 * e, 2.7 * e, 55 * e, 48.7 * e), fill=MARCA)
    lapiz.polygon(puntos([(14.5, 40.7), (32, 61), (49.5, 40.7)]), fill=MARCA)
    lapiz.ellipse((16.5 * e, 10 * e, 47.5 * e, 41 * e), fill='white')
    lapiz.polygon(puntos([(20, 17), (34, 17), (34, 12.5), (44, 20), (34, 27.5), (34, 23), (20, 23)]), fill=MARCA)
    lapiz.polygon(puntos([(44, 34), (30, 34), (30, 38.5), (20, 31), (30, 23.5), (30, 28), (44, 28)]), fill=MARCA)
    return capa.resize((lado, lado), Image.LANCZOS)


def _datos(provider):
    chips = []
    if provider.verificado_publico:
        chips.append(('verificado', 'Verificado'))
    if provider.whatsapp_confirmado:
        chips.append(('sello', 'WhatsApp confirmado'))
    if provider.registro_salud_comprobado:
        chips.append(('sello', 'Registro de salud comprobado'))
    if provider.licencia_sec_comprobada:
        chips.append(('sello', 'Licencia SEC comprobada'))
    chips += [('rubro', _limpio(c.name)) for c in provider.rubros[1:]]
    chips += [('modalidad', m) for m in provider.modalities]
    return {
        'rubro': _limpio(provider.category.name).upper(),
        'comuna': _limpio(provider.commune.name),
        'nombre': _limpio(provider.business_name) or 'ServiPlace',
        'subtitulo': _limpio(provider.profession_title or provider.sector),
        'descripcion': _limpio(provider.short_description),
        'chips': chips,
        'foto': _abrir(provider.foto) if provider.foto else None,
        'trabajos': [f for f in (_abrir(i.image) for i in list(provider.images.all())[:3]) if f],
    }


def _filas_de_chips(chips, ancho):
    """Reparte los chips en hasta dos filas; los que no caben se quedan fuera."""
    fuente = _fuente(NEGRITA, 26)
    filas, fila, usado = [], [], 0
    for tipo, texto in chips:
        largo = fuente.getlength(texto) + 44
        if fila and usado + 12 + largo > ancho:
            filas.append(fila)
            if len(filas) == 2:
                return filas
            fila, usado = [], 0
        if largo <= ancho:
            fila.append((tipo, texto, largo))
            usado += (12 if usado else 0) + largo
    if fila:
        filas.append(fila)
    return filas


def _nombre(texto, ancho):
    """El nombre lo más grande posible en dos líneas como máximo."""
    for tamano in (72, 66, 60, 54, 50):
        fuente = _fuente(TITULO, tamano)
        lineas = _partir(texto, fuente, ancho, 3)
        if len(lineas) <= 2:
            return fuente, lineas
    return fuente, _partir(texto, fuente, ancho, 2)


def _tarjeta(img, y0, datos, lineas_descripcion):
    """Dibuja la tarjeta desde y0 y devuelve su alto. Con img=None solo mide."""
    x0, interior = TARJETA_X + RELLENO, TARJETA_ANCHO - 2 * RELLENO
    lapiz = ImageDraw.Draw(img) if img else None
    y = y0 + RELLENO

    # Rubro principal y comuna, como la cabecera de la tarjeta del sitio.
    if lapiz:
        x = x0
        for letra in datos['rubro']:
            lapiz.text((x, y), letra, font=_fuente(NEGRITA, 26), fill=ACENTO, anchor='la')
            x += _fuente(NEGRITA, 26).getlength(letra) + 3
        lapiz.text((x0 + interior, y), datos['comuna'], font=_fuente(TEXTO, 28), fill=GRIS, anchor='ra')
    y += 34 + 34

    # Foto o inicial, nombre y profesión.
    avatar = 164
    ancho_texto = interior - avatar - 36
    fuente_nombre, lineas_nombre = _nombre(datos['nombre'], ancho_texto)
    alto_linea_nombre = int(fuente_nombre.size * 1.08)
    lineas_sub = _partir(datos['subtitulo'], _fuente(TEXTO, 32), ancho_texto, 2) if datos['subtitulo'] else []
    alto_texto = len(lineas_nombre) * alto_linea_nombre + (10 + 40 * len(lineas_sub) if lineas_sub else 0)
    alto_fila = max(avatar, alto_texto)
    if img:
        ya = y + (alto_fila - avatar) // 2
        if datos['foto']:
            _pegar_foto(img, datos['foto'], x0, ya, avatar, avatar, elipse=True)
        else:
            _forma(img, x0, ya, avatar, avatar, '#cffafe', elipse=True)
            lapiz.text((x0 + avatar / 2, ya + avatar / 2), datos['nombre'][0].upper(),
                       font=_fuente(TITULO, 84), fill=ACENTO, anchor='mm')
        yt = y + (alto_fila - alto_texto) // 2
        for linea in lineas_nombre:
            lapiz.text((x0 + avatar + 36, yt), linea, font=fuente_nombre, fill=TINTA, anchor='la')
            yt += alto_linea_nombre
        yt += 10
        for linea in lineas_sub:
            lapiz.text((x0 + avatar + 36, yt), linea, font=_fuente(TEXTO, 32), fill=GRIS, anchor='la')
            yt += 40
    y += alto_fila + 36

    # Lo que hace, en sus palabras.
    lineas = _partir(datos['descripcion'], _fuente(TEXTO, 38), interior, lineas_descripcion)
    if lapiz:
        for i, linea in enumerate(lineas):
            lapiz.text((x0, y + i * 50), linea, font=_fuente(TEXTO, 38), fill=TINTA, anchor='la')
    y += len(lineas) * 50

    # Sellos, otros rubros y modalidades.
    filas = _filas_de_chips(datos['chips'], interior)
    if filas:
        y += 28
        for fila in filas:
            if lapiz:
                x = x0
                for tipo, texto, largo in fila:
                    fondo, letra = CHIPS[tipo]
                    _forma(img, x, y, largo, 52, fondo, radio=26)
                    lapiz.text((x + largo / 2, y + 26), texto, font=_fuente(NEGRITA, 26), fill=letra, anchor='mm')
                    x += largo + 12
            y += 52 + 12
        y -= 12

    # Fotos de trabajos: lo que más convence a quien está mirando.
    if datos['trabajos']:
        y += 36
        lado = (interior - 2 * 16) // 3
        x = x0 + (interior - len(datos['trabajos']) * (lado + 16) + 16) // 2
        if img:
            for foto in datos['trabajos']:
                _pegar_foto(img, foto, x, y, lado, lado, radio=20)
                x += lado + 16
        y += lado

    # El botón de la ficha: dice qué pasa al tocar el enlace.
    y += 40
    if img:
        _forma(img, x0, y, interior, 100, VERDE, radio=22)
        lapiz.text((x0 + interior / 2, y + 50), 'Contactar por WhatsApp', font=_fuente(NEGRITA, 38),
                   fill='white', anchor='mm')
    y += 100 + RELLENO
    return y - y0


def _fondo(img):
    lapiz = ImageDraw.Draw(img)
    for x in range(118, ANCHO, 128):
        lapiz.rectangle((x, 0, x + 9, ALTO), fill=CUADRICULA)
    for y in range(92, ALTO, 102):
        lapiz.rectangle((0, y, ANCHO, y + 9), fill=CUADRICULA)

    # Marca arriba, centrada.
    fuente = _fuente(TITULO, 58)
    ancho_marca = 64 + 16 + fuente.getlength('serviplace')
    x = (ANCHO - ancho_marca) / 2
    logo = _logo(64)
    img.paste(logo, (int(x), 262), logo)
    lapiz.text((x + 80, 294), 'serviplace', font=fuente, fill='white', anchor='lm')
    lapiz.text((ANCHO / 2, 360), 'Profesionales y negocios por comuna', font=_fuente(TEXTO, 30),
               fill='#94a3b8', anchor='mt')

    # Abajo, donde va el sticker de enlace.
    lapiz.text((ANCHO / 2, 1536), 'Ficha completa y contacto en', font=_fuente(TEXTO, 32), fill='#cbd5e1', anchor='mt')
    fuente = _fuente(TITULO, 60)
    ancho_pildora = fuente.getlength('serviplace.cl') + 80
    _forma(img, (ANCHO - ancho_pildora) / 2, 1590, ancho_pildora, 96, MARCA, radio=22)
    lapiz.text((ANCHO / 2, 1638), 'serviplace.cl', font=fuente, fill='#0b1216', anchor='mm')


def dibujar(provider):
    """JPEG de 1080x1920 con la ficha. Conviene pasar el perfil con categoría,
    comuna, otros rubros e imágenes ya cargados (select/prefetch_related)."""
    datos = _datos(provider)
    zona = ZONA_ABAJO - ZONA_ARRIBA
    for lineas in (4, 3, 2):  # la descripción cede líneas antes que la tarjeta se salga
        alto = _tarjeta(None, 0, datos, lineas)
        if alto <= zona:
            break
    img = Image.new('RGB', (ANCHO, ALTO), FONDO)
    _fondo(img)
    y0 = ZONA_ARRIBA + max(0, (zona - alto) // 2)
    _forma(img, TARJETA_X, y0, TARJETA_ANCHO, alto, 'white', radio=36)
    _tarjeta(img, y0, datos, lineas)

    salida = io.BytesIO()
    img.save(salida, 'JPEG', quality=88, optimize=True, progressive=True)
    return salida.getvalue()
