# Ciclo N — evidencia de la revisión

    REPO      <ruta absoluta>  ·  <url del remote>
    RAMA      <rama>
    BASE      <sha completo>
    CABEZA    <sha completo>
    ENTORNO   <base de datos, .env, servicios externos tocados>

Comprobado con `git rev-parse --show-toplevel` y `git rev-parse HEAD`:
sí / no. Si no coincide, el veredicto es INCONCLUSO y no sigue nada más.

## Comandos ejecutados de verdad

Solo lo que se corrió. Si algo no se pudo correr, va en "No verificado" con
el motivo, nunca acá.

| Comando | Resultado |
|---|---|
| `.\verificar.ps1` | |
| | |

## Hallazgos

Identificador estable `C<ciclo>-<n>`. **No cambia nunca**: si un hallazgo
reaparece en otro ciclo, se reabre con el mismo número.

### C<N>-1 · [P?][BLOQUEA o NO BLOQUEA] Título

    Criterio de TASK.md contra el que atenta:
    Ubicación:
    Evidencia:
    Cómo reproducirlo:
    Impacto:
    Dirección sugerida:

Un P2 solo puede marcarse BLOQUEA si nombra el criterio de `TASK.md` contra
el que atenta. Si no se puede nombrar, no bloquea.

## No verificado

Qué no se pudo comprobar y **qué haría falta** para poder hacerlo. Esto no se
convierte en PASS por defecto.

## Auditoría de criterios

    [x] PASS          A1 · manage.py check
    [ ] FAIL          B1 · freno de fuerza bruta
    [?] NO VERIFICADO B6 · ...
    [-] N/A           ...

## Estado de los hallazgos del ciclo anterior

    C<N-1>-1  cerrado / abierto / reabierto  — cómo se comprobó

## Veredicto

PASS · FAIL · INCONCLUSO

Una línea de por qué.
