# STATUS.md

**Ciclo:** 1 — entregado para revisión
**Escrito por:** Claude
**Fecha:** 05-09-2026

    REPO      C:\Users\diego\Desktop\backup-gogodevs\Proyectos GoGoDevS\GoGoCRM\serviplace
              https://github.com/GoGo-DevS/serviplace  (privado)
    RAMA      main
    BASE      ab6721c6a9b98c640ddbbc08b4588ccd361f9f80
    CABEZA    (el commit de esta entrega — ver `git log -1`)
    ENTORNO   SQLite local. Sin Postgres, sin Render, sin dominio, sin envíos.
              No se tocó ninguna base de producción ni ninguna API paga.

Comprobado antes de tocar nada: `git rev-parse --show-toplevel` termina en
`/serviplace`, remote `GoGo-DevS/serviplace`, rama `main`, árbol limpio.

---

## Qué se cambió

| Criterio | Qué se hizo | Archivo |
|---|---|---|
| D1 | El listado pagina de a 24, con controles que conservan los filtros | `directory/views.py`, `templates/directory/provider_list.html` |
| D4 | El hueco de fotos solo se muestra si el perfil tiene dueño | `templates/directory/provider_detail.html` |
| E2 | Tamaño táctil mínimo de 44 px en controles, solo con `pointer:coarse` | `static/css/site.css` |
| B1-B5 | 13 pruebas de seguridad del autoservicio | `accounts/tests.py` (nuevo) |
| B3, C, D1, D4 | 18 pruebas del directorio público | `directory/tests.py` |

**Nada de esto cambia el comportamiento para el usuario salvo D1, D4 y E2.**
El resto es evidencia sobre código que ya existía.

## Comandos ejecutados, y su resultado

| Comando | Resultado |
|---|---|
| `manage.py check` | 0 issues |
| `manage.py makemigrations --check --dry-run` | sin cambios pendientes |
| `manage.py test` | **31 pruebas, OK** (antes: 0) |
| `manage.py check --deploy` con `DEBUG=False` | 0 errores, 1 advertencia (`SECURE_HSTS_PRELOAD`) |
| `.\verificar.ps1` completo | **todos los criterios pasan** |
| Chrome real a 390 y 1440 px | 0 desbordes, 0 imágenes rotas, 0 errores de JS |

`/servicios/` pasó de **162.604 px** de alto a **11.986 px**.

## Criterios de TASK.md

    [x] A1  manage.py check
    [x] A2  migraciones al día
    [x] A3  8 rutas responden lo esperado
    [x] A4  sin errores de JavaScript
    [x] B1  fuerza bruta: 429 al pasar el tope, y el login correcto sigue funcionando
    [x] B2  la contraseña nunca llega a LoginAttempt
    [x] B3  lo que publica un usuario no se ejecuta
    [x] B4  el antispam marca y NO rechaza
    [x] B5  nadie edita el perfil de otro (ni por GET ni por POST)
    [x] B6  check --deploy sin errores
    [x] C1  ningún activo con teléfono sintético
    [x] C2  todo activo con fuente y URL
    [x] C3  la ficha ofrece reclamar el perfil o pedir la baja
    [x] D1  el listado pagina
    [x] D2  el botón fijo no tapa texto
    [x] D3  sin comuna duplicada
    [x] D4  no se anuncian fotos que nadie puede subir
    [x] E1  0 desbordes
    [x] E2  nada táctil bajo 44 px
    [x] E3  0 imágenes rotas

## Comprobación al revés — qué prueba protege qué

Hecha en un **worktree de git aparte** (`git worktree add --detach` sobre el
commit BASE), sin tocar la copia de trabajo. El worktree se eliminó al
terminar.

| Arreglo desarmado | Pruebas que fallan |
|---|---|
| Paginación fuera de la vista | 3 de D1 |
| Orden sin desempate por `pk` | `test_el_orden_TERMINA_en_un_campo_unico` |
| El hueco de fotos para todos | `test_un_perfil_scrapeado_no_muestra_el_hueco` |

## 🔴 Lo que hay que saber para revisar esto

Tres cosas que no se ven en el diff y que cambian cómo hay que leer el ciclo.

### 1. Las 13 pruebas de `accounts` PASAN contra el código viejo

Se corrieron sobre el commit BASE y dieron **13/13 OK**. No detectan ningún
defecto arreglado, porque **no había defecto**: el freno de fuerza bruta, el
antispam y la autorización ya estaban escritos por la sesión autónoma.

Lo que hacen es **fijar** ese comportamiento. Es exactamente el objetivo
declarado del ciclo ("convertir código escrito en evidencia"), pero sería
deshonesto presentarlas como si hubieran cazado algo.

### 2. El defecto del orden al paginar NO se puede reproducir en SQLite

Se intentó dos veces: primero con 29 prestadores de nombres únicos, después
con 29 de nombre idéntico. En ambos casos SQLite devolvió un orden estable, y
la prueba pasaba **con el desempate y sin él**.

En PostgreSQL —que es donde va a correr— `ORDER BY` sobre columnas que empatan
no garantiza orden entre consultas, y ahí sí un prestador sale en dos páginas
y otro en ninguna. Como el comportamiento no es observable acá, la prueba fija
lo único que sí lo es: **que el orden termine en una columna única**. Es una
prueba de implementación, y se aceptó porque la alternativa era no proteger
nada. Está documentado en su docstring.

### 3. Tres defectos de mis propias pruebas, encontrados y corregidos

Se documentan porque una prueba que acusa al código correcto es peor que no
tenerla: manda a "arreglar" algo que funciona.

- **El honeypot nunca se rellenaba.** `_registrar(HONEYPOT_FIELD='x')` pasa el
  keyword **literal** `"HONEYPOT_FIELD"`, no el nombre real del campo. La
  prueba fallaba sobre un control que funcionaba bien. Corregido con `**{...}`.
- **Se pedía que "enviar rápido" marcara spam.** Suma 30 y el umbral es 40:
  por diseño no basta, y está bien que no baste — el autocompletado del
  navegador llena un formulario en menos de un segundo. La prueba ahora fija
  esa decisión al revés: rápido solo **no** marca, rápido + otra señal sí.
- **El detector de XSS pasó por tres versiones.** Buscar la subcadena
  `onerror=alert(1)` fallaba sobre HTML correctamente escapado; buscar
  `<script` fallaba siempre por los scripts legítimos del sitio; y un regex
  más fino daba falso positivo porque cruzaba dentro de un
  `<meta content="…">`. La versión final **parsea** el HTML con `html.parser`
  y compara contra una línea base limpia. Tiene dos pruebas propias que le
  inyectan HTML ejecutable para confirmar que lo detecta — sin eso, la suite
  podría estar dando verde sobre un sitio vulnerable.

## Lo que NO se verificó

- **Nada contra PostgreSQL.** Local es SQLite. Ver el punto 2 de arriba: es
  justamente donde vive el riesgo del orden.
- **Nada en un teléfono real ni en Safari.** Todo es Chrome de escritorio con
  el viewport forzado a 390 px. `pointer: coarse` se comporta distinto en un
  aparato de verdad.
- **El sitio nunca se desplegó.** `check --deploy` se corrió con variables
  simuladas; no hay evidencia de que arranque en Render.
- **`SECURE_HSTS_PRELOAD`** queda en `False` a propósito: con HSTS de 30 días,
  entrar a la lista de preload es prematuro y salir de ella es lento. Si Codex
  lo considera bloqueante, se discute con el criterio, no se activa a ciegas.
- **La accesibilidad más allá del tamaño táctil**: no se revisó contraste,
  foco visible ni jerarquía de encabezados. Está fuera de `TASK.md`.

## Fuera de alcance, sin tocar

Como declara `TASK.md`: el rediseño premium, el importador multi-fuente
(Facebook Marketplace / Yapo / LinkedIn), el despliegue y la migración de
Cloudinary a R2.

---

**No se declara PASS.** El veredicto lo da Codex en `REVIEW.md`, con su
evidencia en `revisiones/ciclo-1.md`.
