# TASK.md — Ciclo 1

## Alcance — verificar esto ANTES de revisar

    REPO      C:\Users\diego\Desktop\backup-gogodevs\Proyectos GoGoDevS\GoGoCRM\serviplace
              https://github.com/GoGo-DevS/serviplace  (privado)
    RAMA      main
    BASE      65e935f8   (el andamiaje del loop; el ciclo 1 arranca acá)
    CABEZA    — la llena Claude al entregar —
    ENTORNO   SQLite local (db.sqlite3). Sin Postgres, sin Render, sin dominio.
              NO se toca Neon: es otro repositorio.
              NO hay envíos de ningún tipo en este proyecto.

⚠️ Este repositorio es git **independiente** y vive dentro de GoGoCRM.
`git remote -v` desde una subcarpeta puede contestar el remote del padre.
Comprobar con `git rev-parse --show-toplevel`; tiene que terminar en
`/serviplace`.

Si algo de arriba no coincide: veredicto `INCONCLUSO`, y no se revisa nada más.

---

**Objetivo del ciclo:** que lo que la sesión autónoma dejó a medias quede
**probado**, y que los defectos que se ven al abrir el sitio desaparezcan.

No es un ciclo de features nuevas. Es el ciclo que convierte "el código está
escrito" en "hay evidencia de que funciona".

## Por qué este ciclo y no otro

La sesión del 04-09 escribió el freno de fuerza bruta, el antispam, los
reportes de perfil y los headers de seguridad — y **cero pruebas**. Un
control de seguridad sin una prueba que falle al desarmarlo no es un control:
es una intención. Además paró a mitad y dejó el sitio sin arrancar, cosa que
nadie detectó hasta que Diego quiso verlo.

## Criterios de aceptación

Cada uno se mide con `.\verificar.ps1`. Si un criterio no lo mide el script,
no cuenta como PASS.

### A. El sitio arranca y responde

- [ ] **A1** `python manage.py check` → 0 issues.
- [ ] **A2** `makemigrations --check --dry-run` → sin cambios pendientes.
      (El modelo y las migraciones no pueden estar desalineados: ya pasó que
      una migración agregaba campos que el modelo no tenía.)
- [ ] **A3** Estas rutas responden lo que corresponde, sin excepción:
      `/` 200 · `/servicios/` 200 · `/sumate/` 302 · `/cuenta/registro/` 200 ·
      `/cuenta/login/` 200 · `/sitemap.xml` 200 · `/robots.txt` 200 ·
      la ficha de un prestador cualquiera 200.
- [ ] **A4** Ninguna página del punto A3 registra error de JavaScript en la
      consola del navegador.

### B. Seguridad — lo que ya está escrito, ahora probado

- [ ] **B1** Fuerza bruta: `LOGIN_MAX_INTENTOS` fallos desde la misma IP
      dentro de `LOGIN_VENTANA_MINUTOS` → el siguiente POST a
      `/cuenta/login/` responde **429**. Un login correcto ANTES del tope
      sigue funcionando.
- [ ] **B2** `LoginAttempt` **nunca** guarda la contraseña. Prueba: enviar un
      login fallido con una contraseña reconocible y comprobar que esa cadena
      no aparece en ningún campo de la fila creada.
- [ ] **B3** XSS: publicar un prestador cuyo nombre y descripción contengan
      `<script>alert(1)</script>` y `"><img src=x onerror=alert(1)>`. En la
      ficha renderizada esas cadenas aparecen **como texto**; el HTML no
      contiene un `<script>` ni un `onerror` inyectado.
- [ ] **B4** Antispam: un POST de registro con el campo trampa relleno, o
      enviado en menos de los segundos mínimos, **se guarda igual** pero
      marcado (`spam_flag=True`) y **no se publica activo**. No se rechaza:
      un falso positivo rechazado es un prestador real perdido en silencio.
- [ ] **B5** Autorización: un usuario autenticado **no** puede editar el
      perfil de otro. `POST /cuenta/mi-perfil/<slug-ajeno>/editar/` → 403 o
      404, y el objeto no cambia.
- [ ] **B6** `check --deploy` con `DEBUG=False` no arroja ningún warning de
      severidad ERROR.

### C. Datos — nada falso se publica

- [ ] **C1** Ningún `Provider` con `is_active=True` tiene teléfono con el
      patrón sintético `5691111`.
- [ ] **C2** Todo `Provider` con `is_active=True` tiene `source_name` y
      `source_url` no vacíos. Sin eso no se puede responder de dónde salió un
      dato publicado sobre un negocio real.
- [ ] **C3** Un perfil scrapeado (sin `owner`) muestra en su ficha la vía
      para reclamarlo o pedir su baja. Es lo que hace legítimo publicar
      información pública: que el dueño pueda actuar sobre ella.

### D. Los defectos que se ven al abrir el sitio

Medidos el 05-09 con Chrome real. Los cuatro son visibles sin herramientas.

- [ ] **D1** `/servicios/` **pagina**. Hoy mide 162.000 px de alto en un
      teléfono: los 361 prestadores en una sola página. Criterio:
      `scrollHeight < 20000` a 390 px, y existe navegación entre páginas.
- [ ] **D2** En la ficha, el botón fijo de WhatsApp **no tapa** texto al
      final del scroll. Criterio: con la página abajo del todo, ningún
      elemento con texto queda cubierto por el botón.
- [ ] **D3** No aparece la comuna duplicada ("Maipú, Maipú"). Criterio: en la
      ficha, el nombre de la comuna no aparece dos veces seguidas separado
      por coma.
- [ ] **D4** La caja "Sin fotos publicadas aún" **no** se muestra en perfiles
      scrapeados sin dueño. Un perfil que nunca va a tener foto no debe
      anunciar que le falta: se lee como que el sitio está a medio hacer.

### E. Sin desbordes ni regresiones visuales

- [ ] **E1** A 390 y 1440 px, en home, listado y ficha:
      `scrollWidth === clientWidth` (0 px de desborde horizontal).
- [ ] **E2** A 390 px, ningún elemento interactivo (`a`, `button`, `input`,
      `select`) mide menos de 44 px de alto.
- [ ] **E3** 0 imágenes rotas (`complete && naturalWidth === 0`).

## Fuera de alcance de este ciclo

Se nombran para que no se cuelen como hallazgos bloqueantes:

- El rediseño premium completo (fase 3 del plan original).
- El importador multi-fuente (Facebook Marketplace / Yapo / LinkedIn) — está
  descrito en `CLAUDE.md`, es el ciclo siguiente.
- El despliegue a Render y el dominio.
- Migrar de Cloudinary a R2.

Si Codex encuentra algo de esta lista, va como **P3/NIT**, no como bloqueante.

## Cómo se verifica

    .\verificar.ps1              todo
    .\verificar.ps1 -Rapido      salta la parte del navegador

El script deja `verificacion.txt` con la salida cruda. Cada criterio imprime
su identificador (A1, B3, …) para poder citarlo en `REVIEW.md`.
