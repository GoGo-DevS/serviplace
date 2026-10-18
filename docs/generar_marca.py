"""Sistema de marca ServiPlace (18-10-2026): lo mejor de las variantes A y B de ChatGPT,
con la paleta turquesa (opción 3), dibujado en vectores propios.

  A · pin con dos flechas (busco / ofrezco) -> logo principal y cabecera
  B · "sp" con la p hecha pin                -> favicon, ícono de app y redes

Genera en static/img/marca/: SVG del ícono A, PNG de favicon/apple-touch/512,
logos horizontales claro y oscuro, el monograma y la imagen para compartir.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(sys.argv[1])
DEST = RAIZ / 'static' / 'img' / 'marca'
DEST.mkdir(parents=True, exist_ok=True)

TURQUESA = '#06B6D4'
PROFUNDO = '#0E7490'
TINTA = '#1B1F24'
PIN = 'M32 3C19.3 3 9 13.1 9 25.7 9 42.2 32 61 32 61s23-18.8 23-35.3C55 13.1 44.7 3 32 3z'
FLECHAS = 'M20 17h14v-4.5L44 20l-10 7.5V23H20zM44 34H30v4.5L20 31l10-7.5V28h14z'


def icono_a(fondo_pin=TURQUESA, circulo='#fff', flechas=TURQUESA, tam=64):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{tam}" height="{tam}">'
            f'<path d="{PIN}" fill="{fondo_pin}"/><circle cx="32" cy="25.5" r="15.5" fill="{circulo}"/>'
            f'<path d="{FLECHAS}" fill="{flechas}"/></svg>')


# SVG del ícono A (sin fuentes: sirve en cualquier parte)
(DEST / 'serviplace-icono.svg').write_text(icono_a(), encoding='utf-8')
(DEST / 'serviplace-icono-blanco.svg').write_text(icono_a('#fff', '#fff', TINTA), encoding='utf-8')


def app_icon(tam):
    """Guía de marca: pin blanco con flechas turquesa sobre cuadrado turquesa redondeado."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{tam}" height="{tam}">'
            f'<rect width="100" height="100" rx="22" fill="{TURQUESA}"/>'
            f'<g transform="translate(18 16) scale(1.0)"><path d="{PIN}" fill="#fff"/>'
            f'<path d="{FLECHAS}" fill="{TURQUESA}"/></g></svg>')

FUENTES = ('<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800'
           '&family=Atkinson+Hyperlegible:wght@400;700&family=IBM+Plex+Mono:wght@600&display=swap" rel="stylesheet">')


def monograma(tam, radio=0.23):
    """B: "s" en la tipografía de la marca + "p" dibujada: asta y pin girado 45°
    cuya punta se une al asta, con el hueco del pin en turquesa."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{tam}" height="{tam}">
  <rect width="100" height="100" rx="{radio*100}" fill="{TURQUESA}"/>
  <text x="11" y="66" font-family="Bricolage Grotesque" font-weight="800" font-size="62" letter-spacing="-3" fill="{TINTA}">s</text>
  <rect x="50" y="31.5" width="11" height="54.5" rx="2.5" fill="{TINTA}"/>
  <g transform="translate(70 47) rotate(45) scale(.7) translate(-32 -25.7)"><path d="{PIN}" fill="{TINTA}"/></g>
  <circle cx="70" cy="46.5" r="6.6" fill="{TURQUESA}"/>
</svg>"""


def lockup(oscuro=False, ancho=1200, alto=360):
    fondo = TINTA if oscuro else '#ffffff'
    texto = '#ffffff' if oscuro else TINTA
    icono = icono_a('#fff', '#fff', TINTA) if oscuro else icono_a()
    return f"""<!doctype html><html><head><meta charset="utf-8">{FUENTES}<style>
body{{margin:0;width:{ancho}px;height:{alto}px;display:flex;align-items:center;justify-content:center;gap:34px;background:{fondo}}}
svg{{width:220px;height:220px}}
span{{font-family:'Bricolage Grotesque';font-weight:800;font-size:170px;letter-spacing:-.055em;color:{texto};line-height:1}}
</style></head><body>{icono}<span>serviplace</span></body></html>"""


def pagina(svg, tam, fondo='transparent'):
    return f"""<!doctype html><html><head><meta charset="utf-8">{FUENTES}<style>
html,body{{margin:0;width:{tam}px;height:{tam}px;background:{fondo};overflow:hidden}}svg{{display:block}}
</style></head><body>{svg}</body></html>"""


CUADRAS = """background:
  radial-gradient(closest-side,#cdeff5 97%,transparent 100%) 84% 28%/300px 200px no-repeat,
  repeating-linear-gradient(90deg,transparent 0 78px,#fff 78px 86px),
  repeating-linear-gradient(0deg,transparent 0 60px,#fff 60px 67px),#e5e9ee;"""

OG = f"""<!doctype html><html><head><meta charset="utf-8">{FUENTES}<style>
body{{margin:0;width:1200px;height:630px;overflow:hidden;font-family:'Atkinson Hyperlegible',sans-serif}}
.mapa{{position:absolute;inset:-40%;transform:rotate(-13deg);{CUADRAS}}}
.card{{position:absolute;left:64px;top:64px;width:720px;background:#fff;border-radius:28px;padding:42px 48px;
box-shadow:0 30px 60px -30px rgba(27,31,36,.5)}}
.marca{{display:flex;align-items:center;gap:12px;font-family:'Bricolage Grotesque';font-weight:800;font-size:44px;letter-spacing:-.05em;color:{TINTA}}}
.marca svg{{width:56px;height:56px}}
h1{{font-family:'Bricolage Grotesque';font-weight:800;font-size:64px;line-height:.98;letter-spacing:-.045em;margin:24px 0 16px;color:{TINTA}}}
h1 u{{text-decoration:none;background:linear-gradient(transparent 62%,#a5f3fc 62%)}}
p{{font-size:27px;color:#3a4047;margin:0;line-height:1.35}}
.pie{{position:absolute;right:64px;bottom:56px;background:{TURQUESA};color:{TINTA};border-radius:18px;padding:18px 26px;
font-family:'IBM Plex Mono';font-weight:600;font-size:24px;letter-spacing:.03em}}
</style></head><body><div class="mapa"></div>
<div class="card"><div class="marca">{icono_a()}serviplace</div>
<h1>¿Buscas o ofreces un servicio <u>en tu comuna</u>?</h1>
<p>Maestros y profesionales independientes. Contacto directo por WhatsApp, sin comisión.</p></div>
<div class="pie">serviplace.cl</div></body></html>"""

TRABAJOS = [
    (pagina(icono_a(tam=32), 32), 'favicon-32.png', 32, 32),
    (pagina(icono_a(tam=512), 512), 'serviplace-icono-512.png', 512, 512),
    (pagina(app_icon(180), 180), 'apple-touch-icon.png', 180, 180),
    (pagina(app_icon(512), 512), 'serviplace-app-512.png', 512, 512),
    (pagina(app_icon(1080), 1080), 'serviplace-perfil-1080.png', 1080, 1080),
    (pagina(monograma(512, .22), 512), 'serviplace-sp-512.png', 512, 512),
    (pagina(monograma(1080, .22), 1080), 'serviplace-sp-perfil-1080.png', 1080, 1080),
    (lockup(False), 'serviplace-logo-horizontal.png', 1200, 360),
    (lockup(True), 'serviplace-logo-horizontal-oscuro.png', 1200, 360),
    (OG, '../og-serviplace.png', 1200, 630),
]

with sync_playwright() as p:
    nav = p.chromium.launch()
    for html, nombre, ancho, alto in TRABAJOS:
        pag = nav.new_page(viewport={'width': ancho, 'height': alto})
        pag.set_content(html)
        pag.wait_for_load_state('networkidle')
        pag.evaluate('document.fonts.ready')
        pag.wait_for_timeout(500)
        pag.screenshot(path=str(DEST / nombre), omit_background=nombre.startswith(('favicon', 'apple', 'serviplace-sp', 'serviplace-icono', 'serviplace-app', 'serviplace-perfil')))
        pag.close()
    nav.close()

for f in sorted(DEST.iterdir()):
    print(f.name, f.stat().st_size // 1024, 'KB')
print('og', (DEST.parent / 'og-serviplace.png').stat().st_size // 1024, 'KB')
