# STATUS.md

**Ciclo:** 0 — montaje del loop
**Escrito por:** Claude
**Fecha:** 05-09-2026

## Qué se hizo en este ciclo

No se implementó ningún criterio de `TASK.md`. Se construyó lo que faltaba
para que el loop pueda funcionar, y se midió la línea de partida.

El diagrama del workflow dice:

    CLAUDE IMPLEMENTA → VERIFICACIÓN AUTOMATIZADA → CODEX REVISA

**Ese paso del medio no existía.** El repositorio tenía tres archivos de test
vacíos y ni una sola prueba. Sin verificación automatizada, Codex tendría que
reproducir a mano cada criterio en cada vuelta, y el límite de 3 ciclos no
alcanzaría para converger.

Tampoco existía `TASK.md`, así que no había nada contra qué auditar: una
revisión sin criterios de aceptación termina siendo un intercambio de
opiniones sobre gusto.

Se agregaron:

| Archivo | Qué es |
|---|---|
| `AGENTS.md` | El contrato: quién escribe qué, qué tiene prohibido cada agente, cómo se cierra un hallazgo |
| `TASK.md` | Los criterios del ciclo 1. Todos falsables y todos medidos por el script |
| `verificar.ps1` | La verificación automatizada. La corren los dos agentes |
| `verificacion/medir_navegador.py` | Mide en un Chrome real lo que el test client no puede ver: desbordes, tamaños táctiles, botones fijos que tapan texto |

## Línea de partida, medida

`.\verificar.ps1` — 05-09-2026. Salida cruda en `verificacion.txt`.

    [PASS] A1  manage.py check
    [PASS] A2  migraciones al día
    [FAIL] B/C la suite corre pero NO HAY NI UNA PRUEBA
    [FAIL] B6  check --deploy arroja errores
    [PASS] C1 C2  nada sintético ni sin fuente está publicado (361 activos)
    [PASS] A3  8 rutas responden lo esperado
    [PASS] A4  sin errores de JavaScript
    [PASS] E1  0 desbordes a 390 y 1440 px
    [FAIL] E2  controles bajo 44 px: menú 40, "Ver perfil" 40, WhatsApp 40/36,
               "Reclamar perfil" 24
    [PASS] E3  0 imágenes rotas
    [FAIL] D1  /servicios/ mide 162.604 px de alto, sin paginación
    [PASS] D2  el botón fijo no tapa texto
    [PASS] D3  sin comuna duplicada
    [FAIL] D4  un perfil scrapeado muestra "Sin fotos publicadas aún"
    [PASS] C3  la ficha ofrece reclamar el perfil o pedir su baja

**3 bloques fallando.** Ninguno es ruido: los tres son trabajo real del
ciclo 1.

## Dos defectos del propio verificador, encontrados y corregidos

Se documentan porque un verificador que reporta defectos inexistentes es peor
que no tener verificador — y ambos habrían hecho perder una vuelta entera del
loop discutiendo cosas que no pasaban.

1. **A1 y A2 fallaban por el entorno, no por el proyecto.** Python 3.13 arranca
   su REPL nuevo cuando cree tener consola y, llamado desde PowerShell, muere
   con `WinError 0: la operación se completó correctamente` **antes de
   ejecutar nada**. `manage.py check` pasaba perfecto por otra vía. Corregido
   con `PYTHON_BASIC_REPL=1`.

2. **El criterio E2 estaba mal definido.** Medía *cualquier* enlace bajo 44 px,
   así que marcaba "← Volver a servicios", que es un enlace dentro de una línea
   de texto: cumplirlo habría obligado a inflar la tipografía del contenido.
   Ahora mide solo lo que la gente aprieta — botones, campos, y enlaces
   pintados como botón o dentro de navegación. Los hallazgos que quedan (menú
   40 px, "Reclamar perfil" 24 px) son legítimos.

## Lo que NO se verificó

Dicho derecho, porque el contrato lo exige:

- **Nada de seguridad se probó todavía.** B1–B5 son exactamente el trabajo del
  ciclo 1. El código del freno de fuerza bruta, el antispam y los reportes
  está escrito, pero **no hay una sola prueba que falle al desarmarlo**. Hasta
  que la haya, "el sitio es seguro" es una intención, no un hecho.
- **B6 falla y no se investigó el detalle.** Se sabe que `check --deploy`
  arroja errores con `DEBUG=False`; cuáles exactamente es parte del ciclo 1.
- **Nada se probó en un teléfono de verdad ni en Safari.** Todo es Chrome de
  escritorio con el viewport forzado.
- **Nada se probó contra PostgreSQL.** Local es SQLite. El sitio nunca se
  desplegó.

## Por qué se cortó la sesión autónoma del 04-09

Sin confirmar. Commiteó la fase 1 (purga de sintéticos y seed real de Google
Maps), entró a la fase 2 y paró a las 19:16 con 448 líneas sin commitear en 6
archivos, sin dejar bitácora. Dejó tres referencias a código que nunca
escribió y el sitio no arrancaba — nadie lo detectó hasta que Diego quiso
verlo. Eso está arreglado (commit `f2854b0`).

**Es el argumento más concreto a favor de este loop:** el trabajo se dio por
hecho sin que nada lo comprobara.

## Siguiente paso

El ciclo 1 está definido en `TASK.md` y su línea de partida medida arriba.
Claude implementa; después `.\verificar.ps1`; después Codex escribe
`REVIEW.md`.
