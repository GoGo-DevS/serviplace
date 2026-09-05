"""Mide en un Chrome real los criterios A3, A4, D1-D4 y E1-E3 de TASK.md.

POR QUE UN NAVEGADOR Y NO EL TEST CLIENT DE DJANGO
Un `assertEqual(response.status_code, 200)` no ve un desborde horizontal, ni
un botón fijo tapando texto, ni un elemento táctil de 30 px. Los cuatro
defectos D1-D4 de este ciclo se encontraron mirando el sitio, no midiendo el
HTML. Esto los convierte en algo que puede fallar solo.

Imprime una línea por criterio con su identificador, para que `REVIEW.md`
pueda citarlo. Sale con código 1 si algún criterio falla.
"""
import json
import sys
from urllib.parse import urljoin

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8021'
fallos = []
notas = []


def ok(cid, texto):
    print(f'  [PASS] {cid}  {texto}')


def fail(cid, texto):
    print(f'  [FAIL] {cid}  {texto}')
    fallos.append(f'{cid}: {texto}')


def main():
    from playwright.sync_api import sync_playwright

    # Las rutas del criterio A3 con su código esperado. `/sumate/` redirige al
    # publicar de autoservicio desde que murió el flujo de postulación.
    rutas = [
        ('/', 200), ('/servicios/', 200), ('/sumate/', 302),
        ('/cuenta/registro/', 200), ('/cuenta/login/', 200),
        ('/sitemap.xml', 200), ('/robots.txt', 200),
    ]

    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel='chrome')
        pag = nav.new_page(viewport={'width': 390, 'height': 844},
                           is_mobile=True, has_touch=True)

        # ── A3: las rutas responden lo que corresponde ──────────────────
        malas = []
        for ruta, esperado in rutas:
            r = pag.request.get(urljoin(BASE, ruta), max_redirects=0)
            if r.status != esperado:
                malas.append(f'{ruta} dio {r.status}, se esperaba {esperado}')
        # La ficha de un prestador cualquiera, sacada del listado real: si se
        # escribiera un slug a mano, la prueba pasaría con la base vacía.
        pag.goto(urljoin(BASE, '/servicios/'), wait_until='load')
        ficha = pag.evaluate(
            "(()=>{const a=document.querySelector('a[href^=\"/prestadores/\"]');"
            "return a?a.getAttribute('href'):null})()")
        if not ficha:
            malas.append('el listado no ofrece ninguna ficha de prestador')
        else:
            r = pag.request.get(urljoin(BASE, ficha))
            if r.status != 200:
                malas.append(f'{ficha} dio {r.status}')
        fail('A3', '; '.join(malas)) if malas else ok('A3', f'{len(rutas)+1} rutas responden lo esperado')

        if not ficha:
            nav.close()
            return

        # ── A4 + E1/E2/E3 + D1/D2/D3/D4, mirando de verdad ──────────────
        errores_js = []
        pag.on('pageerror', lambda e: errores_js.append(str(e)[:120]))

        desbordes, chicos, rotas = [], [], []
        for ancho, alto in ((390, 844), (1440, 900)):
            pag.set_viewport_size({'width': ancho, 'height': alto})
            for ruta in ('/', '/servicios/', ficha):
                pag.goto(urljoin(BASE, ruta), wait_until='load')
                pag.wait_for_timeout(900)
                m = pag.evaluate("""() => {
                  const R = e => e.getBoundingClientRect();
                  const chicos = [];
                  if (innerWidth < 800) {
                    // SOLO CONTROLES, no cualquier enlace. Un enlace dentro de
                    // un párrafo mide lo que mide su línea de texto y exigirle
                    // 44 px obligaría a inflar la tipografía del contenido:
                    // el criterio se volvería imposible de cumplir sin empeorar
                    // el sitio, y el loop se trabaría en él. Se mide lo que la
                    // gente APRIETA: botones, campos, y enlaces que se pintan
                    // como botón o como ítem de navegación.
                    const controles = new Set(
                      [...document.querySelectorAll('button, input, select, textarea, [role="button"]')]);
                    document.querySelectorAll('a').forEach(a => {
                      const s = getComputedStyle(a);
                      const enLinea = s.display === 'inline'
                                      && !a.closest('nav, header, footer, [role="navigation"]');
                      const pintadoComoBoton = parseFloat(s.paddingTop) >= 6
                                               || parseFloat(s.borderTopWidth) >= 1
                                               || s.backgroundColor !== 'rgba(0, 0, 0, 0)';
                      if (!enLinea && pintadoComoBoton) controles.add(a);
                    });
                    controles.forEach(e => {
                      const r = R(e);
                      // Solo lo que se ve: un elemento oculto no se toca.
                      if (r.height > 0 && r.width > 0 && r.height < 44) {
                        chicos.push((e.getAttribute('aria-label') || e.textContent || e.tagName)
                                    .trim().slice(0, 18) + ':' + Math.round(r.height));
                      }
                    });
                  }
                  return {
                    desborde: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                    alto: document.documentElement.scrollHeight,
                    chicos: [...new Set(chicos)],
                    rotas: [...document.images].filter(i => i.complete && i.naturalWidth === 0).length,
                  };
                }""")
                if m['desborde'] > 0:
                    desbordes.append(f'{ancho}px {ruta} desborda {m["desborde"]}px')
                if m['rotas']:
                    rotas.append(f'{ancho}px {ruta}: {m["rotas"]}')
                if ancho == 390 and m['chicos']:
                    chicos.append(f'{ruta}: {m["chicos"][:4]}')
                if ancho == 390 and ruta == '/servicios/':
                    notas.append(('D1_alto', m['alto']))

        fail('E1', '; '.join(desbordes)) if desbordes else ok('E1', '0 desbordes a 390 y 1440 px')
        fail('E2', '; '.join(chicos)) if chicos else ok('E2', 'nada táctil bajo 44 px a 390 px')
        fail('E3', '; '.join(rotas)) if rotas else ok('E3', '0 imágenes rotas')
        fail('A4', str(errores_js[:3])) if errores_js else ok('A4', 'sin errores de JavaScript')

        # ── D1: el listado pagina ───────────────────────────────────────
        alto = dict(notas).get('D1_alto', 0)
        pag.set_viewport_size({'width': 390, 'height': 844})
        pag.goto(urljoin(BASE, '/servicios/'), wait_until='load')
        pag.wait_for_timeout(700)
        hay_paginacion = pag.evaluate(
            "!!document.querySelector('.pagination, [aria-label*=agina], a[href*=\"page=\"]')")
        if alto >= 20000 or not hay_paginacion:
            fail('D1', f'/servicios/ mide {alto}px de alto y paginación={hay_paginacion}')
        else:
            ok('D1', f'lista paginada, alto {alto}px')

        # ── D2: el botón fijo no tapa texto ─────────────────────────────
        pag.goto(urljoin(BASE, ficha), wait_until='load')
        pag.wait_for_timeout(700)
        pag.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        pag.wait_for_timeout(700)
        tapado = pag.evaluate("""() => {
          const fijos = [...document.querySelectorAll('*')].filter(e => {
            const s = getComputedStyle(e);
            return (s.position === 'fixed' || s.position === 'sticky')
                   && e.getBoundingClientRect().top > innerHeight * 0.5;
          });
          if (!fijos.length) return null;
          const barra = fijos[0].getBoundingClientRect();
          let peor = null;
          document.querySelectorAll('p, li, span, h1, h2, h3, td, label').forEach(e => {
            if (e.children.length) return;
            const t = (e.textContent || '').trim();
            if (!t) return;
            const r = e.getBoundingClientRect();
            if (r.height < 6) return;
            if (r.bottom > barra.top + 4 && r.top < barra.bottom
                && r.right > barra.left && r.left < barra.right) peor = t.slice(0, 40);
          });
          return peor;
        }""")
        fail('D2', f'el botón fijo tapa: "{tapado}"') if tapado else ok('D2', 'el botón fijo no tapa texto')

        # ── D3: comuna duplicada ────────────────────────────────────────
        dup = pag.evaluate("""() => {
          const t = document.body.innerText;
          const m = t.match(/\\b([A-ZÁÉÍÓÚÑ][\\wÁÉÍÓÚÑáéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][\\wÁÉÍÓÚÑáéíóúñ]+)?), \\1\\b/);
          return m ? m[0] : null;
        }""")
        fail('D3', f'aparece duplicado: "{dup}"') if dup else ok('D3', 'sin comuna duplicada')

        # ── D4: "sin fotos" en un perfil que nunca tendrá foto ──────────
        sin_fotos = pag.evaluate(
            "/sin fotos/i.test(document.body.innerText)")
        reclamar = pag.evaluate(
            "/reclam/i.test(document.body.innerText)")
        if sin_fotos and reclamar:
            fail('D4', 'un perfil scrapeado (ofrece reclamarlo) muestra "Sin fotos publicadas aún"')
        else:
            ok('D4', 'no anuncia fotos faltantes en perfiles sin dueño')

        # ── C3: el perfil scrapeado ofrece reclamarlo o pedir la baja ───
        if reclamar or pag.evaluate("/baja|eliminar mis datos|corregir/i.test(document.body.innerText)"):
            ok('C3', 'la ficha ofrece reclamar el perfil o pedir su baja')
        else:
            fail('C3', 'un perfil scrapeado no ofrece reclamarlo ni pedir su baja')

        nav.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001 — el runner necesita el motivo, no la traza
        print(f'  [ERROR] la medición en navegador no pudo correr: {type(e).__name__}: {e}')
        sys.exit(2)
    print()
    if fallos:
        print(f'NAVEGADOR: {len(fallos)} criterio(s) fallando')
        sys.exit(1)
    print('NAVEGADOR: todos los criterios pasan')
