"""Pasa a PNG los íconos del sitio para dibujar la historia de Instagram (21-11-2026).

La historia se arma con Pillow en el servidor, que no dibuja SVG. Para que use los
MISMOS íconos que la tarjeta del sitio, este script los fotografía desde sus fuentes
(directory/templatetags/rubros.py y directory/_sellos.html, con el CSS real) y los
guarda acá como PNG transparentes. Se corre a mano cuando cambie un ícono:

    ../venv/Scripts/python.exe directory/fuentes/iconos/generar.py
"""
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITIO = AQUI.parents[2]
sys.path.insert(0, str(SITIO))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_URL'] = ''  # no necesita base: solo plantillas
import django  # noqa: E402

django.setup()
from django.template import Context, Template  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from directory.templatetags.rubros import _TRAZOS  # noqa: E402

CSS = ''.join(f'<link rel="stylesheet" href="{(SITIO / "static" / r).as_uri()}">'
              for r in ('vendor/bootstrap/bootstrap.min.css', 'css/site.css', 'css/cuadra.css'))


class _Falso:
    whatsapp_confirmado = registro_salud_comprobado = True
    licencia_sec_comprobada = False


def svg(nombre, color):
    return (f'<svg viewBox="0 0 24 24" width="96" height="96" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{_TRAZOS[nombre]}</svg>')


sellos = Template(open(SITIO / 'templates/directory/_sellos.html', encoding='utf-8').read()).render(
    Context({'provider': _Falso()}))
with sync_playwright() as pw:
    nav = pw.chromium.launch()
    pg = nav.new_page(device_scale_factor=3)
    for nombre in _TRAZOS:  # rubros en el acento; modalidades en gris pizarra
        color = '#3a4047' if nombre in ('casa', 'local', 'pantalla') else '#0e7490'
        pg.set_content(f'<body style="margin:0;background:transparent">{svg(nombre, color)}</body>')
        pg.locator('svg').screenshot(path=str(AQUI / f'{nombre}.png'), omit_background=True)
    import re
    for sello in ('whatsapp', 'salud'):
        trozo = re.search(r'<span class="[^"]*" data-tip="[^"]*"[^>]*data-sello="%s">.*?</span></span>' % sello, sellos, re.S)
        if not trozo:
            raise SystemExit(f'no encontré el sello {sello} en _sellos.html')
        # Desde un archivo y no con set_content: una página en blanco no puede leer CSS local.
        tmp = AQUI / '_tmp.html'
        tmp.write_text(f'<html><head><meta charset="utf-8">{CSS}</head><body style="margin:0;background:transparent">'
                       f'<div id="caja" style="position:relative;width:40px;height:40px;padding:2px">'
                       f'<div class="ficha-tags" style="margin:0">{trozo.group(0)}</div></div></body></html>', encoding='utf-8')
        pg.goto(tmp.as_uri(), wait_until='networkidle')
        pg.add_style_tag(content='.sello-wa-logo,.sello-salud-ico .sello-ico{width:2rem!important;height:2rem!important}'
                                 '[data-tip]::after,[data-tip]::before{display:none!important}')
        pg.locator('#caja').screenshot(path=str(AQUI / f'sello-{sello}.png'), omit_background=True)
    nav.close()
(AQUI / '_tmp.html').unlink(missing_ok=True)
print('ok', len(list(AQUI.glob('*.png'))), 'íconos')
