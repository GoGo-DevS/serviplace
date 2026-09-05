# AGENTS.md — el contrato del loop

Dos agentes trabajan sobre este repositorio. Este archivo es lo único que
ambos aceptan como reglas del juego.

    CLAUDE IMPLEMENTA
          ↓
    VERIFICACIÓN AUTOMATIZADA   ( .\verificar.ps1 )
          ↓
    CODEX REVISA                ( escribe REVIEW.md )
          ↓
    FAIL → CLAUDE ARREGLA → verificar de nuevo → CODEX revisa de nuevo
          ↓
    PASS

## Los archivos, y quién escribe cada uno

| Archivo         | Lo escribe | Para qué |
|-----------------|-----------|----------|
| `TASK.md`       | Diego / Claude | Los criterios de aceptación del ciclo. **Es contra esto que se audita.** |
| `verificar.ps1` | Claude    | La verificación automatizada. Los dos la corren. |
| `STATUS.md`     | Claude    | Qué se implementó, qué se verificó, y qué NO se verificó. |
| `REVIEW.md`     | Codex     | El veredicto: PASS o FAIL, con evidencia. |

Nadie escribe el archivo de otro. Claude no toca `REVIEW.md`; Codex no toca
`STATUS.md`.

## La regla que hace que esto funcione

**Un criterio de aceptación tiene que poder FALLAR.**

Si un criterio no se puede medir, no entra a `TASK.md`. "Que se vea premium"
no es un criterio: no hay evidencia que lo resuelva, así que el loop no
converge y las tres vueltas se gastan discutiendo gusto.

    ✗  "el listado se ve bien en el celular"
    ✓  "GET /servicios/ a 390 px: scrollWidth === clientWidth, y
        document.documentElement.scrollHeight < 20000"

    ✗  "el registro es seguro"
    ✓  "9 intentos fallidos de login desde la misma IP en 15 min: el 9º
        responde 429"

Cuando algo es genuinamente de criterio (diseño, redacción), se decide ANTES
en `TASK.md` con una referencia concreta, no se discute durante la revisión.

## Lo que Claude tiene prohibido

- Declarar PASS. El veredicto es de Codex.
- Escribir en `STATUS.md` que algo se verificó sin haberlo corrido. Si no se
  pudo verificar, se escribe **NO VERIFICADO** y por qué. Convertir en
  silencio "no lo probé" en "funciona" es lo que este loop existe para evitar.
- Arreglar un hallazgo cambiando la prueba en vez del código.
- Tocar `TASK.md` a mitad de un ciclo para acomodar lo que se implementó.

## Lo que Codex tiene prohibido

- Reportar un comando que no ejecutó.
- Subir la severidad de una preferencia personal a P1.
- Reimplementar la tarea en vez de demostrar el defecto.

## Cómo se cierra un hallazgo

Cada hallazgo P0/P1/P2 de `REVIEW.md` se cierra de UNA de estas tres formas,
y se dice cuál en `STATUS.md`:

1. **Arreglado** — con la prueba que falla sin el arreglo. Se indica el commit.
2. **No es un defecto** — con la evidencia que lo desmiente. Si Codex tenía
   razón y Claude se equivoca al defenderse, se arregla y punto.
3. **Aceptado, fuera de alcance** — solo si Diego lo decide. Queda escrito en
   `TASK.md` como criterio de un ciclo futuro, no se pierde.

Una prueba no está lista cuando pasa: está lista cuando se comprobó que
**falla sin el arreglo**. Eso se hace desarmando el arreglo, corriendo, y
volviendo a armarlo. Se anota en `STATUS.md` cuáles se comprobaron así.

## Límite

3 ciclos. Si al terminar el 3º quedan bloqueantes, el veredicto se queda en
FAIL y se documentan sin empezar una cuarta vuelta: eso es una señal de que
`TASK.md` pedía demasiado o pedía algo mal definido, y lo resuelve Diego, no
otra ronda de revisión.

## Contexto del repositorio

ServiPlace, directorio de prestadores de servicios por comuna en Chile.
Django 5.2, SQLite en local. Léase `CLAUDE.md` para la historia del producto,
las decisiones tomadas y la bitácora. Entorno:

    ..\venv\Scripts\python.exe          el intérprete (es el de GoGoCRM)
    .\verificar.ps1                     la verificación completa
    python manage.py runserver 8020     para mirarlo
