# AGENTS.md — el contrato del loop

Dos agentes trabajan sobre este repositorio. Este archivo es lo único que
ambos aceptan como reglas del juego.

> **v2 — 05-09-2026.** Incorpora los cinco ajustes que pidió Codex al revisar
> la v1, y el hueco que él mismo señaló al final: *el prompt no conecta a los
> agentes ni ejecuta nada; falta definir cómo nos entregamos los cambios y el
> reporte*. Está resuelto en "El canal" y en "Alcance de la revisión".

## Alcance de la revisión — se declara, no se supone

**Lo primero de cada ciclo.** Sin esto no arranca nada, y no es burocracia:
en este equipo ya se trabajó sobre una copia muerta de un repositorio que
respondía el `git remote` del padre y parecía legítima. Se perdió una tanda
entera.

Cada `TASK.md` abre declarando:

    REPO      ruta absoluta + URL del remote
    RAMA      la rama
    BASE      el commit desde el que se revisa (SHA completo)
    CABEZA    el commit hasta el que se revisa (lo llena Claude al entregar)
    ENTORNO   qué base de datos, qué .env, qué servicios externos se tocan

Codex verifica que está parado en ese repositorio y ese commit **antes** de
mirar una sola línea. Si no coincide, el veredicto es `INCONCLUSO` y no se
revisa nada más.

⚠️ **Este repositorio (`serviplace`) es git independiente y vive DENTRO de
GoGoCRM.** `git remote -v` desde una subcarpeta puede contestar el remote del
padre. Comprobar siempre `git rev-parse --show-toplevel`.

## Tres veredictos, no dos

| Veredicto | Cuándo |
|---|---|
| **PASS** | Sin bloqueantes abiertos y los criterios aplicables verificados |
| **FAIL** | Queda al menos un bloqueante con evidencia |
| **INCONCLUSO** | No se pudo comprobar lo esencial: falta sesión, credencial, entorno o servicio |

`INCONCLUSO` no es un empate cortés. Es el veredicto correcto cuando el
entorno impide juzgar, y **no se convierte en PASS por defecto**. Un ciclo
puede cerrarse INCONCLUSO diciendo exactamente qué hizo falta para poder
juzgar; eso lo resuelve Diego, no otra vuelta de revisión.

## Gravedad y bloqueo son dos cosas distintas

La v1 metía todos los P2 en "hallazgos bloqueantes" y a la vez decía que un
P2 solo bloquea si compromete el resultado pedido. Se contradecía. Ahora cada
hallazgo lleva las dos etiquetas, por separado:

    [P1][BLOQUEA]     defecto grave que impide entregar
    [P2][BLOQUEA]     calidad seria que compromete lo que TASK.md pidió
    [P2][NO BLOQUEA]  calidad seria que NO compromete el objetivo del ciclo
    [P3][NO BLOQUEA]  mejora menor

Todo P0 y P1 bloquea siempre. Un P2 bloquea solo si Codex explica **contra
qué criterio de `TASK.md`** atenta. Si no puede nombrar el criterio, no
bloquea — va a la lista de arrastre y se decide en el ciclo siguiente.

## Revisar no puede tener efectos reales

**Regla dura, sin excepciones tácitas.** Verificar no puede:

- mandar un mensaje a un cliente o prospecto real (WhatsApp, Instagram, correo)
- escribir en una base de producción
- emitir un cobro, una boleta o un pago
- publicar en una red social
- gastar cuota de una API paga

Toda verificación corre contra **base de test o SQLite descartable**, con
datos de prueba, y con los envíos apagados. Si un criterio SOLO se puede
comprobar con un efecto real, no se ejecuta a escondidas: se marca
`INCONCLUSO`, se dice qué haría falta, y **Diego autoriza esa corrida en
concreto** — no "las corridas de este tipo".

En GoGoCRM esto es literal: el `.env` de la raíz apunta a Neon, que es
producción con los datos de todos los clientes.

## El canal — cómo nos entregamos las cosas

No hay conexión entre los agentes. **El repositorio es el canal**, y lo que
no está commiteado no existe para el otro.

    Claude entrega:   implementa → .\verificar.ps1 → escribe STATUS.md
                      → commit → push
                      → avisa: "ciclo N entregado, CABEZA <sha>"

    Codex revisa:     git pull → comprueba REPO/RAMA/BASE/CABEZA
                      → corre .\verificar.ps1 él mismo
                      → escribe REVIEW.md → commit → push
                      → avisa: "ciclo N revisado, VEREDICTO"

Nadie escribe el archivo del otro. Si los dos tocan el repositorio a la vez,
el segundo hace `git pull --rebase` antes de comitear: `STATUS.md` y
`REVIEW.md` son archivos distintos, así que no chocan.

Diego es quien pasa el aviso entre los dos. Es un paso manual y está bien que
lo sea: es donde él decide si el ciclo sigue.

## Evidencia archivada, con identificadores estables

Cada revisión deja su rastro en `revisiones/ciclo-<N>.md`, con:

- REPO, RAMA, BASE, CABEZA
- los comandos que se ejecutaron **de verdad** y su salida
- cada hallazgo con un identificador estable: `C<ciclo>-<n>`, por ejemplo
  `C1-3`. Ese identificador **no cambia nunca**: así el ciclo 2 puede decir
  "C1-3 cerrado, con la prueba `test_x` que falla sin el arreglo" y se puede
  seguir el hilo sin releer todo.

Un hallazgo cerrado no se vuelve a abrir con otro número. Si reaparece, es el
mismo `C1-3` reabierto, y eso ya dice algo por sí solo.

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
