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
import math
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

# Subirlo cuando cambie el dibujo: cambia la versión de todas las historias
# (Provider.version_historia) y nadie recibe la imagen vieja guardada.
DISENO = 5  # 23-11-2026: geometría fija; portada vertical recortada desde arriba

ANCHO, ALTO = 1080, 1920
FUENTES = Path(__file__).resolve().parent / 'fuentes'
ICONOS = FUENTES / 'iconos'            # los mismos íconos del sitio, en PNG (iconos/generar.py)
LOGO_SEC = Path(__file__).resolve().parents[1] / 'static' / 'img' / 'sellos' / 'sec.png'
TITULO = 'plus-jakarta-sans-800.ttf'    # la fuente de títulos del sitio desde el 20-11-2026
ETIQUETA = 'plus-jakarta-sans-700.ttf'
TEXTO = 'atkinson-hyperlegible-400.ttf'
NEGRITA = 'atkinson-hyperlegible-700.ttf'

FONDO, CUADRICULA = '#1b1f24', '#2a3038'
TINTA, GRIS, ACENTO, MARCA, VERDE = '#1b1f24', '#5a6068', '#0e7490', '#06b6d4', '#0f7a40'
AZUL_CHECK = '#1d8cf8'
SUAVE, ETIQ_GRIS, DESC = '#f1f5f9', '#64748b', '#475569'

# Geometría FIJA (23-11-2026): la tarjeta mide y se ubica siempre igual, falte o no información.
TARJETA_X, TARJETA_Y, TARJETA_ANCHO, TARJETA_ALTO = 58, 368, 964, 1140
BANDA = 300
RELLENO = 48
RADIO = 36

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


def _check(lado):
    """La insignia azul de Verificado (la misma del sitio): un sello festoneado con
    un visto blanco. Se dibuja a 8x y se achica, para que el borde salga suave."""
    k = 8
    t = lado * k
    capa = Image.new('RGBA', (t, t), (0, 0, 0, 0))
    lapiz = ImageDraw.Draw(capa)
    c, radio, bulto = t / 2, t * 0.37, t * 0.13
    for i in range(8):
        a = math.tau * i / 8
        x, y = c + t * 0.345 * math.cos(a), c + t * 0.345 * math.sin(a)
        lapiz.ellipse((x - bulto, y - bulto, x + bulto, y + bulto), fill=AZUL_CHECK)
    lapiz.ellipse((c - radio, c - radio, c + radio, c + radio), fill=AZUL_CHECK)
    lapiz.line([(t * 0.31, t * 0.52), (t * 0.44, t * 0.64), (t * 0.70, t * 0.38)], fill='white',
               width=int(t * 0.095), joint='curve')
    return capa.resize((lado, lado), Image.LANCZOS)


@lru_cache(maxsize=64)
def _icono(nombre, lado, opacidad=1.0):
    """Un ícono del sitio en PNG (directory/fuentes/iconos/), achicado a `lado`.
    Sin el archivo devuelve None y la historia sale igual, sin ese ícono."""
    try:
        imagen = Image.open(ICONOS / f'{nombre}.png').convert('RGBA')
    except OSError:
        return None
    imagen = imagen.resize((lado, lado), Image.LANCZOS)
    if opacidad < 1:
        alfa = imagen.getchannel('A').point(lambda v: int(v * opacidad))
        imagen.putalpha(alfa)
    return imagen


@lru_cache(maxsize=4)
def _logo_sec(alto):
    try:
        imagen = Image.open(LOGO_SEC).convert('RGBA')
    except OSError:
        return None
    return imagen.resize((round(imagen.width * alto / imagen.height), alto), Image.LANCZOS)


def _pegar(img, capa, x, y):
    if capa is not None:
        img.paste(capa, (int(x), int(y)), capa)


def _degradado(ancho, alto, arriba, abajo):
    """Degradado vertical entre dos colores hex, como el fondo de la tarjeta sin foto."""
    a = tuple(int(arriba[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(abajo[i:i + 2], 16) for i in (1, 3, 5))
    capa = Image.new('RGB', (1, alto))
    for y in range(alto):
        t = y / max(1, alto - 1)
        capa.putpixel((0, y), tuple(round(a[c] + (b[c] - a[c]) * t) for c in range(3)))
    return capa.resize((ancho, alto))


def _mascara_arriba(ancho, alto, radio):
    """Bordes redondeados solo arriba: la franja de imagen va pegada al borde de la tarjeta."""
    completa = _mascara(ancho, alto + radio * 2, radio)
    return completa.crop((0, 0, ancho, alto))


def _separar_nombre(texto):
    """"Karla Barrientos | Asesoría en formalización…" trae el nombre y una descripción
    en el mismo campo: se separan para que el nombre no empuje todo lo demás."""
    if '|' in texto:
        nombre, resto = texto.split('|', 1)
        return nombre.strip() or texto, resto.strip()
    return texto, ''


def _donde_atiende(provider):
    if provider.atiende_toda_la_region and provider.commune_id and provider.commune.region_id:
        return f'Toda la {_limpio(provider.commune.region.name)}'
    otras = provider.comunas_cobertura
    base = _limpio(provider.commune.name)
    if not otras:
        return base
    if len(otras) <= 2:
        nombres = [base] + [_limpio(c.name) for c in otras]
        return ', '.join(nombres[:-1]) + ' y ' + nombres[-1]
    return f'{base} y {len(otras)} comunas más'


def _datos(provider):
    from directory.templatetags.rubros import nombre_icono_rubro
    sellos = [n for n, si in (('whatsapp', provider.whatsapp_confirmado),
                              ('salud', provider.registro_salud_comprobado),
                              ('sec', provider.licencia_sec_comprobada)) if si]
    modalidades = [n for n, si in (('casa', provider.attends_home), ('local', provider.attends_office),
                                   ('pantalla', provider.attends_online)) if si]

    # El recuadro de abajo siempre tiene 2 o 3 filas, todas con datos reales del perfil:
    # primero la formación; si falta, dónde atiende, cómo atiende y sus otros rubros.
    filas = []
    if provider.profession_title:
        titulo = _limpio(provider.profession_title)
        if provider.graduation_year:
            titulo += (f' · se titula en {provider.graduation_year}' if provider.is_student
                       else f' · titulado/a en {provider.graduation_year}')
        filas.append(('TÍTULO', titulo))
    if provider.institution:
        filas.append(('ESTUDIÓ EN', _limpio(provider.institution)))
    if provider.health_registry and provider.registro_salud_comprobado:
        filas.append(('REGISTRO', f'N° {_limpio(provider.health_registry)}'))
    if len(filas) < 3:
        filas.append(('ATIENDE EN', _donde_atiende(provider)))
    if len(filas) < 3 and provider.modalities:
        filas.append(('MODALIDAD', ' · '.join(provider.modalities)))
    otros = [_limpio(c.name) for c in provider.rubros[1:]]
    if len(filas) < 3 and otros:
        filas.append(('TAMBIÉN', ', '.join(otros)))
    if len(filas) < 2:  # vale para todos: el botón de la ficha abre su WhatsApp
        filas.append(('CONTACTO', 'Directo por WhatsApp'))

    nombre, descriptor = _separar_nombre(_limpio(provider.business_name) or 'ServiPlace')
    imagenes = list(provider.images.all())
    portada = next((i for i in imagenes if i.is_cover), imagenes[0] if imagenes else None)
    return {
        'icono_rubro': nombre_icono_rubro(provider.category),
        'rubro': _limpio(provider.category.name).upper(),
        'comuna': _limpio(provider.commune.name).upper(),
        'nombre': nombre,
        'subtitulo': descriptor or _limpio(provider.sector_limpio or provider.commune.name),
        'verificado': provider.verificado_publico,
        'descripcion': _limpio(provider.short_description),
        'filas': filas[:3],
        'sellos': sellos,
        'modalidades': modalidades,
        'foto': _abrir(provider.foto) if provider.foto else None,
        'portada': _abrir(portada.image) if portada else None,
    }


def _nombre(texto, ancho):
    """El nombre lo más grande posible en dos líneas; si aun así no cabe, con puntos suspensivos."""
    for tamano in (60, 56, 52, 48, 44, 40):
        fuente = _fuente(ETIQUETA, tamano)
        lineas = _partir(texto, fuente, ancho, 3)
        if len(lineas) <= 2:
            return fuente, lineas
    return fuente, _partir(texto, fuente, ancho, 2)


def _espaciado(lapiz, x, y, texto, fuente, color, aire):
    """Texto en mayúsculas con aire entre letras, como las etiquetas del sitio.
    Devuelve dónde termina; con lapiz=None solo mide."""
    for letra in texto:
        if lapiz:
            lapiz.text((x, y), letra, font=fuente, fill=color, anchor='lm')
        x += fuente.getlength(letra) + aire
    return x


def _franja(datos):
    """La imagen de arriba de la tarjeta, siempre del mismo tamaño. Una foto apaisada se
    recorta al centro. Una vertical (un pantallazo del celular o un afiche) se recorta desde
    arriba (saltando las barras del celular) a todo el ancho: ahí suele estar lo importante, y mostrarla entera en una franja
    de 300 px dejaba un celular diminuto (23-11-2026, la ficha de Diego). Sin foto: el ícono
    del rubro sobre el celeste."""
    ancho, alto = TARJETA_ANCHO, BANDA
    foto = datos['portada']
    if foto is None:
        franja = _degradado(ancho, alto, '#eaf7fa', '#d6f1f7')
        icono = _icono(datos['icono_rubro'], 140, 0.55)
        if icono is not None:
            franja.paste(icono, ((ancho - 140) // 2, (alto - 140) // 2), icono)
        return franja
    vertical = foto.width < foto.height
    # 0.12 y no 0: en un pantallazo de celular lo primero son la barra de estado y la del navegador.
    return ImageOps.fit(foto, (ancho, alto), Image.BICUBIC, centering=(0.5, 0.12 if vertical else 0.4))


def _tarjeta(img, datos):
    """La tarjeta de la historia, con geometría FIJA (23-11-2026): mide y se ubica
    siempre igual, y cada bloque tiene su alto reservado aunque falte el dato.
    Diego: "que sean todas iguales, independiente de si falta info"."""
    x0, y0 = TARJETA_X + RELLENO, TARJETA_Y
    interior = TARJETA_ANCHO - 2 * RELLENO
    lapiz = ImageDraw.Draw(img)

    # 1. Franja de imagen (0 a BANDA).
    img.paste(_franja(datos), (TARJETA_X, y0), _mascara_arriba(TARJETA_ANCHO, BANDA, RADIO))
    # Línea fina bajo la imagen: una foto clara (un pantallazo blanco) no se funde con la tarjeta.
    lapiz.rectangle((TARJETA_X, y0 + BANDA - 2, TARJETA_X + TARJETA_ANCHO - 1, y0 + BANDA - 1), fill='#dfe5ec')

    # 2. Rubro con su ícono y comuna.
    y = y0 + BANDA + 34
    fuente_etq = _fuente(ETIQUETA, 27)
    _pegar(img, _icono(datos['icono_rubro'], 36), x0, y)
    _espaciado(lapiz, x0 + 48, y + 18, datos['rubro'], fuente_etq, ACENTO, 2)
    ancho_comuna = _espaciado(None, 0, 0, datos['comuna'], fuente_etq, GRIS, 2)
    _espaciado(lapiz, x0 + interior - ancho_comuna, y + 18, datos['comuna'], fuente_etq, GRIS, 2)

    # 3. Avatar, nombre (máx. 2 líneas) con el visto y el subtítulo: alto fijo de 150.
    y += 36 + 30
    avatar, alto_fila = 140, 150
    if datos['foto']:
        _pegar_foto(img, datos['foto'], x0, y + 5, avatar, avatar, radio=32)
    else:
        img.paste(_degradado(avatar, avatar, '#e0f7fb', '#b8ebf3'), (x0, y + 5), _mascara(avatar, avatar, 32))
        lapiz.text((x0 + avatar / 2, y + 5 + avatar / 2), datos['nombre'][0].upper(),
                   font=_fuente(TITULO, 66), fill='#155e75', anchor='mm')
    xt = x0 + avatar + 32
    ancho_texto = interior - avatar - 32
    lado_check = 50 if datos['verificado'] else 0
    fuente_nombre, lineas = _nombre(datos['nombre'], ancho_texto - (lado_check + 12 if lado_check else 0))
    alto_linea = int(fuente_nombre.size * 1.1)
    fuente_sub = _fuente(TEXTO, 30)
    sub = _partir(datos['subtitulo'], fuente_sub, ancho_texto, 1)[0] if datos['subtitulo'] else ''
    alto_bloque = len(lineas) * alto_linea + (44 if sub else 0)
    yt = y + (alto_fila - alto_bloque) // 2
    for i, linea in enumerate(lineas):
        lapiz.text((xt, yt), linea, font=fuente_nombre, fill=TINTA, anchor='la')
        if lado_check and i == len(lineas) - 1:
            caja = lapiz.textbbox((xt, yt), linea, font=fuente_nombre, anchor='la')
            yc = int((caja[1] + caja[3]) / 2 - lado_check / 2)
            img.paste(_check(lado_check), (int(xt + fuente_nombre.getlength(linea) + 12), yc), _check(lado_check))
        yt += alto_linea
    if sub:
        lapiz.text((xt, yt + 6), sub, font=fuente_sub, fill=GRIS, anchor='la')

    # 4. Descripción: siempre el espacio de 3 líneas, aunque use menos.
    y += alto_fila + 28
    for i, linea in enumerate(_partir(datos['descripcion'], _fuente(TEXTO, 34), interior, 3)):
        lapiz.text((x0, y + i * 46), linea, font=_fuente(TEXTO, 34), fill=DESC, anchor='la')

    # 5. Recuadro de datos: alto fijo, 2 o 3 filas reales, centradas en su espacio.
    y += 3 * 46 + 26
    alto_caja = 210
    _forma(img, x0, y, interior, alto_caja, SUAVE, radio=22)
    col = 210
    valor_ancho = interior - 2 * 28 - col
    # Cada valor puede usar 2 líneas mientras el recuadro tenga espacio (máx. 4 líneas en total);
    # si no, las últimas filas quedan en una línea con puntos suspensivos.
    filas = [(etq, _partir(v, _fuente(NEGRITA, 29), valor_ancho, 2)) for etq, v in datos['filas']]
    for i in range(len(filas) - 1, -1, -1):
        if sum(len(v) for _, v in filas) <= 4:
            break
        etq, v = filas[i]
        filas[i] = (etq, _partir(' '.join(v), _fuente(NEGRITA, 29), valor_ancho, 1))
    alto_filas = sum(len(v) * 38 for _, v in filas) + 16 * (len(filas) - 1)
    yy = y + (alto_caja - alto_filas) // 2
    for etq, valores in filas:
        _espaciado(lapiz, x0 + 28, yy + 19, etq, _fuente(ETIQUETA, 21), ETIQ_GRIS, 1.5)
        for j, v in enumerate(valores):
            lapiz.text((x0 + 28 + col, yy + j * 38), v, font=_fuente(NEGRITA, 29), fill=TINTA, anchor='la')
        yy += len(valores) * 38 + 16

    # 6. Sellos y modalidades en íconos, con el botón de WhatsApp: pegados al pie de la tarjeta.
    boton_ancho, alto_pie = 300, 92
    y = TARJETA_Y + TARJETA_ALTO - RELLENO - alto_pie
    x, limite = x0, x0 + interior - boton_ancho - 16
    piezas = [(_logo_sec(54) if s == 'sec' else _icono(f'sello-{s}', 80)) for s in datos['sellos']]
    for nombre in datos['modalidades']:
        cuadro = Image.new('RGBA', (76, 76), (0, 0, 0, 0))
        cuadro.paste(Image.new('RGBA', (76, 76), SUAVE), (0, 0), _mascara(76, 76, 18))
        icono = _icono(nombre, 42)
        if icono is not None:
            cuadro.paste(icono, (17, 17), icono)
        piezas.append(cuadro)
    for pieza in piezas:
        if pieza is None or x + pieza.width > limite:
            continue
        _pegar(img, pieza, x, y + (alto_pie - pieza.height) // 2)
        x += pieza.width + 12
    bx = x0 + interior - boton_ancho
    _forma(img, bx, y, boton_ancho, alto_pie, VERDE, radio=22)
    lapiz.text((bx + boton_ancho / 2, y + alto_pie / 2), 'WhatsApp', font=_fuente(ETIQUETA, 36),
               fill='white', anchor='mm')


def _fondo(img):
    lapiz = ImageDraw.Draw(img)
    for x in range(118, ANCHO, 128):
        lapiz.rectangle((x, 0, x + 9, ALTO), fill=CUADRICULA)
    for y in range(92, ALTO, 102):
        lapiz.rectangle((0, y, ANCHO, y + 9), fill=CUADRICULA)

    # Marca arriba, centrada, justo bajo la zona donde Instagram pone el nombre de la cuenta.
    fuente = _fuente(TITULO, 54)
    ancho_marca = 58 + 14 + fuente.getlength('serviplace')
    x = (ANCHO - ancho_marca) / 2
    logo = _logo(58)
    img.paste(logo, (int(x), 262), logo)
    lapiz.text((x + 72, 291), 'serviplace', font=fuente, fill='white', anchor='lm')

    # Abajo, donde va el sticker de enlace.
    lapiz.text((ANCHO / 2, 1548), 'Ficha completa y contacto en', font=_fuente(TEXTO, 32), fill='#cbd5e1', anchor='mt')
    fuente = _fuente(TITULO, 56)
    ancho_pildora = fuente.getlength('serviplace.cl') + 80
    _forma(img, (ANCHO - ancho_pildora) / 2, 1598, ancho_pildora, 92, MARCA, radio=22)
    lapiz.text((ANCHO / 2, 1644), 'serviplace.cl', font=fuente, fill='#0b1216', anchor='mm')


def dibujar(provider):
    """JPEG de 1080x1920 con la ficha. Conviene pasar el perfil con categoría,
    comuna, otros rubros e imágenes ya cargados (select/prefetch_related)."""
    datos = _datos(provider)
    img = Image.new('RGB', (ANCHO, ALTO), FONDO)
    _fondo(img)
    _forma(img, TARJETA_X, TARJETA_Y, TARJETA_ANCHO, TARJETA_ALTO, 'white', radio=RADIO)
    _tarjeta(img, datos)

    salida = io.BytesIO()
    img.save(salida, 'JPEG', quality=88, optimize=True, progressive=True)
    return salida.getvalue()
