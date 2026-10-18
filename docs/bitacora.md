# Bitácora de ServiPlace (desde el 16-10-2026)

El CLAUDE.md del proyecto no se edita (regla de permisos de Diego); las
entradas nuevas van acá, con el mismo formato.

---
[16-10-2026] — Modo: autónomo ("déjamelo operativo")
Tarea completada: SERVIPLACE EN VIVO en https://serviplace.cl.
  · Dominio comprado por Diego en NIC el 15-10 (vence 15-10-2027). NS ->
    Cloudflare (emerie/graham). Zona Free; @ A 216.24.57.1 y www CNAME
    serviplace-60so.onrender.com, ambos DNS only (gris). SSL lo emite Render.
  · Render: el workspace principal estaba 25/25 servicios. Se creó el
    workspace "ServiPlace" (Hobby, $0, sin tarjeta): cupo propio, 2 dominios
    gratis y no cae si falla el cobro de la cuenta de clientes.
  · Neon: proyecto `serviplace` en la cuenta gratis (org-green-hat), us-east-1,
    junto al servicio (Virginia).
  · R2: bucket `serviplace` + dominio media.serviplace.cl + token limitado a
    ese bucket (Object R/W). Lo creó Diego: el clasificador no deja crearlo.
  · Datos: el build carga `directorio_inicial.json` (361 activos, contadores
    en cero) SOLO en base vacía; después `seed_regiones_chile` dio 0 nuevas.
    Admin "diego" creado por `asegurar_admin`.
Archivos modificados: requirements.txt (storages+boto3, fuera Cloudinary),
  render.yaml, build.sh, cargar_directorio_inicial.py, asegurar_admin.py,
  404.html, 500.html, home.html, directory/tests.py (39 pruebas).
Decisiones tomadas: a producción solo los 361 activos; los 89 ocultos y los
  10 de prueba quedan en `_respaldos-serviplace/serviplace_2026-10-16.json`.
Bugs encontrados/resueltos: la portada decía "verificados manualmente" con
  349 de 361 sin revisar. Corregido + prueba que falla con el texto viejo.
QA en vivo: 13 rutas OK, 361 prestadores, https válido, www y http -> apex,
  los 3 nombres resuelven igual en 1.1.1.1 / 8.8.8.8 / 9.9.9.9.
NO VERIFICADO: subir una foto a R2 de punta a punta (exige crear una cuenta
  o usar el admin en producción). Email Routing de contacto@ sin crear
  (Diego no lo ha aprobado). Render free duerme a los 15 min.
Próxima tarea: probar una foto en el admin; decidir el correo; Search Console.
---

---
[17-10-2026] — Modo: autónomo ("hazlo en modo autónomo, déjala genial")
Tarea completada: SERVIPLACE TAMBIÉN PARA PROFESIONALES INDEPENDIENTES.
  Origen: una kinesióloga de Concepción le dijo a Diego que a los recién
  titulados les habría servido: LinkedIn y las bolsas de empleo no les
  funcionan. Lectura: no necesitan empleador, necesitan CLIENTES. Mismo
  producto (perfil + comuna + WhatsApp), otra audiencia.
  · Categorías en 5 grupos (Category.group): hogar (las 9 de siempre), salud
    (8), educación (4), belleza (2), profesional (4) = 27. `seed_categorias`
    corre en build.sh (idempotente, no pisa lo editado en el admin).
  · Perfil profesional opcional: título, institución, año de titulación,
    registro en la Superintendencia de Salud (enlace al registro público
    para que el paciente lo compruebe; no decimos "verificado") y modalidad
    (domicilio / consulta o local / online).
  · REGLA: categoría de salud + año de titulación futuro = no publica
    (ejercicio ilegal). El estudiante puede publicar clases.
  · Landing /profesionales/ (en sitemap y nav), portada con grupos, chips,
    conteo por especialidad y "Sé el primero en publicar"; listado con
    ?grupo= y estado vacío que invita a publicar. Mensaje de WhatsApp sin
    "cotización". En el teléfono, cada grupo es una fila deslizable:
    portada de 12.500 px a ~6.800.
DEFECTOS QUE ESTABAN EN VIVO, ENCONTRADOS Y CORREGIDOS (con prueba cada uno):
  1. /cuenta/dashboard/ daba 500 a TODO usuario con sesión (es adonde lleva
     el login). Usaba ProviderReport.CLAIM y `claimant`, que la sesión
     autónoma del 04-09 nunca agregó al modelo. -> migración 0009.
  2. "Reclamar perfil" daba 500 (mismo motivo) y además su formulario no
     mandaba ningún campo: habría salido inválido en silencio.
  3. ProviderReport no estaba en el admin: reportes y reclamos invisibles.
     Ahora sí, con la acción "Aprobar reclamo" (no le quita el perfil a
     quien ya es dueño).
  4. Antispam: el formulario de publicar no dibujaba el sello; toda persona
     sumaba 20 ("sin_sello") y con 2 enlaces en la descripción su perfil
     quedaba OCULTO. En el registro el honeypot se veía a la vista con su
     etiqueta "Deja este campo vacío". -> templates/_antispam.html.
  5. Redirección abierta en el registro: ?next=//sitio-ajeno pasaba el
     `startswith('/')`. -> url_has_allowed_host_and_scheme.
  6. El listado decía "24 resultados" con 361 (contaba la página).
  7. El formulario de publicar solo mostraba el error del nombre.
  8. El panel mostraba "—" fijo en visitas y clics, y "estado verificado:
     activo" a cualquiera con un perfil. También "perfils".
  9. "Obtener badge verificado" se mostraba en el perfil AJENO a todo visitante.
Archivos: directory/{models,admin,views,catalogo}.py, migraciones 0008-0009,
  seed_categorias.py, accounts/{forms,views}.py, core/{views,urls,sitemaps}.py,
  settings (SITE_DESCRIPTION), plantillas de portada, landing, listado,
  ficha, tarjeta, formulario, reclamo, panel, base; site.css; build.sh.
Pruebas: 76 (antes 39). Comprobación al revés: 7 mutaciones (regla de salud,
  sello, redirección, campos del reclamo, filtro por grupo, contador, CLAIM)
  -> las 7 hacen fallar su prueba.
Simulación de la actualización de producción sobre una copia del estado de
  Render (0007, 361 perfiles): aplica 0008-0009, 361 intactos, 27 categorías.
QA en Chrome real a 390 y 1440 px: 0 desbordes, 0 imágenes rotas, 0 errores
  de JS, todas las rutas con su código. Lo único bajo 44 px son enlaces de
  texto ("← Volver", "Ver todos →"), el mismo patrón del resto del sitio.
NO VERIFICADO: nada se probó en producción (falta el push de Diego). El
  registro de la Superintendencia (rnpi.superdesalud.gob.cl) respondió 200
  hoy; si cambia de URL, el enlace de la ficha queda roto.
Próxima tarea: push; probar en vivo /profesionales/, publicar un perfil de
  prueba y borrarlo; encuesta de Instagram con la opción nueva.
---

---
[18-10-2026] — Modo: colaborativo (Diego trajo dos análisis de GPT)
Tarea completada: MEDICIÓN DEL EMBUDO + REDISEÑO "CUADRA".
  Decisión de diseño: entre tres caminos renderizados (artifact "Rediseño
  ServiPlace": volante de poste / credencial / cuadra) quedó Cuadra como
  identidad + Credencial como ficha, y el volante para publicidad.
  Respuesta a "¿qué lado falla?": ninguno tiene datos. Oferta = 361 perfiles
  de oficios importados en 4 comunas fuertes (Maipú 82, Las Condes 69,
  Puente Alto 66, La Florida 61), 0 publicados por su dueño, 0 profesionales.
  Demanda ≈ 0 (sin difusión, sin Search Console, sin GA4).
  · Medición (01d00b2): LeadEvent amplía a búsqueda (con conteo de
    resultados), visita clave, registro iniciado, cuenta creada y perfil
    publicado. Bots fuera (Google, vista previa de WhatsApp, curl): antes
    inflaban vistas y clics. Sin IP ni agente: hash diario. Teléfonos
    escritos en el buscador se borran. Panel /cuenta/metricas/ solo staff,
    con la lectura automática A-E del plan de 21 días.
  · Diseño (6c63ca6): tokens nuevos en site.css y la capa static/css/cuadra.css.
    Portada con mapa ilustrativo (lo dice) y pines = comunas con más
    perfiles (cifras reales); buscador "qué + comuna"; franja permanente
    "Quiero publicar mis servicios". Tarjeta-credencial con estado honesto
    (revisado / de su dueño / fuentes públicas, sin revisar). Landing de
    profesionales: el valor del día uno es un link profesional propio para
    compartir (resuelve el incentivo para publicar aunque haya poco tráfico).
Pruebas: 91. QA en Chrome real a 390 y 1440: sin desbordes, imágenes rotas
  ni errores de JS. Portada en el teléfono: 12.500 -> 5.800 px.
NO VERIFICADO EN VIVO: nada de esto (ni 34b299c) está subido. Falta el push.
Próxima tarea: push; dar de alta Search Console (TXT en Cloudflare); elegir
  Maipú como mercado inicial (oferta real + Diego vive ahí) y medir 7 días
  con difusión mínima antes de cualquier campaña.
---

---
[18-10-2026, tarde] — Modo: colaborativo
Tarea completada: PORTADA DE DOS PUERTAS + IMPORTADOS OCULTOS + LOGO/FOTO + QA.
  Pedidos de Diego en orden: (1) los perfiles destacados eran data no
  validada y sin logos: "horrible"; (2) la portada tiene que separar altiro
  al que busca del que ofrece; (3) arreglar problemas visuales tipo cajas de
  texto que no calzan, con QA de UI/UX; (4) tag de GoGoDevS.
  · Decisiones (AskUserQuestion): ocultar los 361 importados; sí a logo/foto.
  · Provider.objects.publicos() = activo + con dueño. Todo lo público parte
    de ahí. Importados: 404, fuera de sitemap y conteos; reclamables por
    /prestadores/<slug>/reclamar/ (para invitarlos).
  · Insignia "Verificado" exige dueño (12 importados traían is_verified=True).
  · Foto: directory/imagenes.py (WebP <100 KB, sin EXIF, exif_transpose).
  · QA con la skill ui-ux-pro-max + auditoría automática en Chrome
    (scratchpad/auditoria_visual.py): 0 problemas reales en 44 revisiones.
DEFECTOS ENCONTRADOS EN ESTA PASADA: login sin clases (campos del navegador),
  errores con aria-describedby a ids inexistentes, doble clic en Publicar
  podía crear dos perfiles, alert() en copiar enlace del panel, texto de
  botones descentrado, franja bajo el pie, mensaje de Django en español de
  España para imagen inválida, emojis en el selector de rubro.
Pruebas: 105.
EFECTO AL PUBLICAR: el directorio público queda con 0 perfiles hasta que
  publiquen los primeros. Pendiente: invitar a los 12 autorizados de Maipú
  con su enlace de reclamo; agregar el bucket `serviplace` al respaldo
  nocturno de R2 (regla 12).
---

---
[18-10-2026, noche] — Modo: colaborativo
Tarea completada: SEO TÉCNICO CON EL CHECKLIST DE JORGE (memoria checklist-seo-tecnico).
  Pedido: "SEO profesional al nivel de Jorge" y "vi enlaces con '?', corregir".
  · URLs limpias: /servicios/<especialidad>/<comuna>/, /servicios/<especialidad>/,
    /servicios/en/<comuna>/, /servicios/<grupo>/. ?categoria/comuna/grupo -> 301.
    ?q= queda noindex + canonical /servicios/.
  · Category.seo_nombre (migraciones 0011 + 0012 de datos): H1/title con la
    palabra que se busca ("Gásfiter en Maipú").
  · directory/seo.py: Organization+WebSite solo en portada, CollectionPage +
    ItemList, BreadcrumbList completa, tipo schema.org por oficio.
  · Listado vacío = 404 + noindex. Sitemap: solo limpias que dan 200.
  · static/img/og-serviplace.png (1200x630) y serviplace-logo.png generados
    con Playwright desde HTML con las fuentes de la marca.
DEFECTOS EN VIVO ENCONTRADOS: paginación con href="??page=2" (la página 2
  nunca cargaba, desde el ciclo 1); el meta robots nunca se imprimía (ninguna
  página tenía noindex); /sumate/ (redirección) estaba en el sitemap; logo del
  schema con STATIC_URL sin barra.
Pruebas: 123 (directory/tests_seo.py: el sitemap se prueba pidiendo cada loc,
  JSON-LD parseado con json.loads). 5 mutaciones detectadas.
NO HECHO / PENDIENTE: Search Console (Diego); PageSpeed medido en vivo;
  contenido por keyword (eso es lo de Jorge, no del sitio).
---

---
[18-10-2026, noche] — Modo: colaborativo
Tarea completada: MARCA SERVIPLACE (logo + paleta turquesa).
  Diego eligió de ChatGPT las variantes A (pin con dos flechas: busca y
  ofrece) y B ("sp"), con la paleta de la opción 3 (turquesa), y después
  mandó su "Guía de marca serviplace en turquesa.png" (Descargas), que
  manda: logo = pin con flechas; ícono de app y favicon = el mismo pin.
  · Dibujado en vectores propios (docs/generar_marca.py regenera todo):
    static/img/marca/ -> serviplace-icono.svg, -blanco.svg, favicon-32,
    apple-touch-icon, serviplace-app-512 (logo del schema), icono-512,
    perfil-1080 (redes), logos horizontales claro/oscuro, y "sp" como
    alternativa. og-serviplace.png regenerada.
  · Paleta: --sp-brand #06B6D4 (logo, pines, botón principal CON TEXTO TINTA,
    6,8:1) y --sp-accent #0E7490 (enlaces, 5,4:1). Blanco sobre #06B6D4 da
    2,4:1: nunca. #9CA3AF de la guía solo para íconos (2,5:1 no sirve para texto).
Pruebas: 123. Auditoría visual: 0 problemas reales.
---

---
[18-10-2026] — Modo: colaborativo
Tarea completada: GA4 + REPORTE SEO SEMANAL DEL CRM.
  · Propiedad GA4 "ServiPlace" 559460692 en la cuenta GoGoDevS (a408968389) de
    diegodinamarca.a; flujo web 16150988442, ID G-RLX75T8KGM (no es secreto).
    settings: GA4_MEASUREMENT_ID; en Render cae al G- aunque el Blueprint no
    sincronice; en local vacío = no carga nada.
  · No se mide: panel, métricas, edición de perfil, login, admin y staff.
  · Eventos: contacto_whatsapp (tarjeta y ficha; es el que cuenta el reporte
    del CRM), search, sign_up y publicar_perfil (se informan una vez, en la
    página siguiente, vía sesión).
  · CRM /reportes/: ServiPlace agregado (sc-domain:serviplace.cl, GA4
    559460692, "envía eventos de contacto"). Sin "Actualizar ahora" todavía.
Pruebas: 130 (core/tests_analitica.py, 7).
PENDIENTE (Diego, el clasificador / la extensión lo bloquean):
  1. GA4 > ServiPlace > Gestión de accesos: reportes-crm@gogodevs-reportes.iam
     .gserviceaccount.com como Lector.
  2. Search Console con diegodinamarca.a: propiedad de dominio serviplace.cl
     (verificación DNS en Cloudflare), enviar /sitemap.xml y agregar la misma
     cuenta de servicio como Restringido.
  3. Cuando lleguen datos (~24 h): marcar contacto_whatsapp, sign_up y
     publicar_perfil como eventos clave (GA4 no deja marcarlos antes).
---

---
[18-10-2026] — Modo: colaborativo
Tarea completada: CV QUE LLENA EL PERFIL.
  Diego: "en /profesionales/ que al registrarse les dé la opción de adjuntar
  CV, y ojalá que el CV llene los datos del formulario".
  · Se adjunta al registrarse (opcional; un CV ilegible NO impide crear la
    cuenta) o arriba de "Publicar mi perfil" (formulario aparte, /cuenta/
    publicar/leer-cv/). PDF (pypdf 6.19.0) o Word (.docx leído a mano, con su
    encabezado); máximo 5 MB, 6 páginas, tope al descomprimir.
  · accounts/cv.py lee POR REGLAS, sin IA: no viaja a terceros ni gasta
    cuota. Propone nombre, nombre profesional, rubro (27, por quién ejerce:
    "kinesióloga" vale más que "kinesiología"), título, institución (la de
    la carrera, no el diplomado), año (el de término; en curso = en blanco),
    registro de salud, comuna (solo de una línea de dirección o la cabecera:
    ni la universidad, ni el empleador, ni el apellido), celular, descripción
    (sección Perfil/Resumen) y modalidades.
  · NO copia dirección, RUT, correo ni fecha de nacimiento; el archivo no se
    guarda; lo propuesto vive en la sesión hasta publicar. Campos llenados
    marcados en turquesa. Términos (sección 4) y FAQ de /profesionales/.
Pruebas: 30 nuevas (accounts/tests_cv.py; PDF y Word armados a mano).
  4 mutaciones detectadas (copiar el correo, guardar el archivo, año de la
  entrada siguiente, comuna del empleador).
---

---
[18-10-2026, noche] — Modo: AUTÓNOMO ("aplícale SEO profesional, trabaja toda la noche")
Tarea completada: SEO PROFESIONAL (técnico + contenido + confianza).
  Diagnóstico: el cuello no es técnico sino de inventario. Con los importados
  ocultos hay 0 perfiles públicos, así que los listados son 404 a propósito y
  del lado de quien busca no hay qué posicionar. Lo posicionable hoy: la
  captación de oferta (profesionales) y la confianza (quien contrata).
  · Rendimiento (Lighthouse móvil en vivo: 71-72, LCP 5,2 s): Bootstrap 5.3.3
    (SRI oficial verificado) y fuentes latin servidos desde el sitio, precarga
    de las 2 fuentes del primer pintado, JS con defer. Antes: ~2,2 s de bloqueo
    por jsdelivr + Google Fonts. Medir de nuevo después del push.
  · serviplace-60so.onrender.com respondía 200 (copia del sitio): ahora 301.
  · /privacidad/ (las condiciones de GA4 la exigen) y /contacto/ con WhatsApp
    por motivo (prometía WhatsApp y correo sin tener ninguno; contacto@ todavía
    no recibe). Intentos de login se borran a los 30 días.
  · 27 páginas /profesionales/<rubro>/ (core/profesiones.py): contenido propio
    por especialidad, credencial RNPI o SEC con enlace oficial, FAQ visible =
    FAQPage, sin precios. 6 guías /guias/ (core/guias.py + templates/guias/,
    redactadas por un agente con datos verificados y revisadas): registro de
    salud, licencia SEC, qué acordar con un maestro, boleta 2026 (15,25%),
    inicio de actividades, primeros clientes. Article con autor con nombre.
  · Schema del perfil: founder con título, institución y registro de salud
    como credenciales; sameAs con web e Instagram. Organización: sameAs
    @serviplace.cl.
  · Perfil: campos sitio web e Instagram (migración 0013 aditiva, rel ugc).
  · core/tests_rastreo.py recorre todo lo público como Screaming Frog. Encontró
    8 enlaces internos a 404: los chips de grupo sin perfiles en la comuna.
    Corregido (chip apagado sin enlace).
  Datos verificados (fuentes): retención 15,25% 2026 (sii.cl, ChileAtiende);
  RNPI en rnpi.superdesalud.gob.cl; licencias SEC A-D / 1-3 y buscador de
  instaladores (ChileAtiende fichas 2662, 2641, 67276).
Pruebas: 199. Mutaciones detectadas: orden de títulos, dominio, FAQ visible.
ERROR PROPIO: el commit 8ba2de2 se hizo con una prueba en rojo por
  `grep ... && git commit` (la lección L8096). Corregido en 6868de2; desde ahí
  el commit depende del código de salida de la suite.
NOTA: el venv local tiene Django 6.0.5 y requirements.txt fija 5.2 (Render).

Instagram @serviplace.cl (pedido de Diego, kit en Descargas):
  6 publicaciones subidas con sus textos (4:5; la 01 corregida: el círculo
  tapaba media línea del texto). Seguidos: gogodevs.cl, colkine, colpsichile,
  colegio_de_nutricionistas, superdesaludchile, sec_chile, sii_chile,
  chileatiende, sercotec_metropolitana, muni_maipu.
  PENDIENTE (Diego, desde el celular): fijar 1-2-3 (la web no tiene "fijar"),
  las 12 historias y las 6 destacadas (Instagram web no sube historias). Las
  historias están revisadas: ninguna tiene texto tapado.
---

---
[18-10-2026, mañana] — Modo: autónomo
Tarea completada: PERFILES DE LOS CLIENTES DE GOGODEVS ("con todo: logo, nombre").
  · Un agente armó la ficha de 16 clientes SOLO desde su sitio público (los
    WhatsApp/teléfonos/IG/correos comparados contra el HTML en vivo; MX de los
    correos revisados). Nada de las notas internas.
  · Entran 10: GoGoDevS, Púas Tatuajes, Salón Amanda, FCO Climatización,
    SafeRoom, Medina4x4, Comercial Villarreal, Popi, Ruta Motors y Dulcecita.
    Fuera por falta de dato verificable: VOA y Travesía (sin comuna), Max
    Services (sin WhatsApp), Vizo Glow (su número no es WhatsApp en el sitio),
    Punto Parcelas (sin comuna) y AZA (organización).
  · Categorías nuevas: Desarrollo web y apps, Tatuajes y piercing, Seguridad
    para el hogar, y el grupo "Tiendas y emprendimientos" (repuestos,
    automotoras, uniformes, repostería) sin página "para profesionales".
    Migración 0014 (solo choices). Dulcecita se estaba inscribiendo y no había
    categoría de repostería: ahora existe.
  · directory/clientes_gogodevs.py + cargar_clientes en build.sh: crea los que
    faltan, nunca pisa, no resucita uno desactivado y se salta a quien ya se
    inscribió solo (mismo WhatsApp o web). Dueño: el admin de Diego. Logos en
    directory/clientes_logos/ (WebP <100 KB, cuadrados, revisados a ojo).
  · La tarjeta dice "Datos de su sitio web oficial", no "Publicado por su
    dueño": no lo publicaron ellos.
  DATOS A CONFIRMAR CON LOS CLIENTES: comuna de Dulcecita, GoGoDevS y SafeRoom
  (sus sitios solo dicen "Santiago"); Medina publica dos WhatsApp (se usó el de
  la barra superior); Villarreal: el dominio sigue en el WordPress viejo.
  DEFECTOS EN SITIOS DE CLIENTES (vistos al pasar): SafeRoom publica
  contacto@saferoomchile.cl y ese dominio NO existe (cualquiera puede
  registrarlo y recibir sus correos); el ícono de FCO corta "CLIMATIZACIÓN";
  rutamotors.cl no apunta a ningún servidor y su og:image es un placeholder.
Pruebas: 207 (directory/tests_clientes.py, 8). Mutación detectada: duplicado
  por WhatsApp.
---

---
[18-10-2026, mediodía] — Diego: "voa es todo chile, travesía también; fco dale
nomás; saferoom déjalo anotado en el CRM".
  · Grupo nuevo "Transporte y traslados" (migración 0015, choices) con Fletes y
    logística (Travesía) y Traslados y turismo (VOA), cada una con su página
    /profesionales/. Comuna base Santiago, "Atención en todo Chile".
  · Logos: el favicon de VOA corta su marca (se usó "VOA" del logo horizontal);
    el de Travesía solo existe en SVG (rasterizado con Chrome headless).
  · SafeRoom: ticket de soporte en el CRM (proyecto 11, Bug, alta) por el correo
    roto contacto@saferoomchile.cl. El proyecto ya tenía la tarea "Email contacto
    real reemplaza placeholder" por hacer.
  Quedan 12 clientes. Fuera: Max Services (sin WhatsApp), Vizo Glow (número no es
  WhatsApp en su sitio), Punto Parcelas (sin comuna), AZA (organización).
Pruebas: 207.
---

---
[18-10-2026, tarde] — Diego: "fotos en cada perfil de mis clientes y GoGoDevS, que
se vea lo máximo poblado; en la ficha hay doble botón de WhatsApp; botones
flotantes de Instagram".
  · 52 fotos de 11 clientes, tomadas de sus sitios por un agente y revisadas a ojo
    en una hoja de contacto: trabajos, productos, locales y vehículos. Fuera las
    generadas con IA (VOA no tiene ni una real; SafeRoom, Travesía, Popi, Medina y
    Ruta Motors tenían varias con metadatos de OpenAI/Gemini) y las que muestran
    a clientes. WebP 1024 px <100 KB en directory/clientes_fotos/ (la primera es
    la portada). cargar_clientes las agrega solo si el perfil no tiene fotos.
  · Tarjetas con foto de portada (prefetch: una consulta para todas, prueba G-04
    con mutación detectada 18 vs 11). En la ficha, las fotos subieron debajo de
    la descripción.
  · El "doble WhatsApp" era el botón de COMPARTIR (verde, decía WhatsApp): ahora
    "Enviar a alguien", neutro, con el menú de compartir del teléfono.
  · Instagram flotante: en la ficha, el del profesional (si tiene); en el resto
    del sitio público, el de @serviplace.cl; en /cuenta/ ninguno.
Pruebas: 212.
---

---
[18-10-2026, noche] — Rendimiento y formulario por rubro (3effdf9, 44446a9).
  · gtag.js bloqueaba ~600 ms en móvil (Lighthouse portada 62): ahora la cola
    dataLayer se arma al tiro y el script carga en la primera interacción o a
    los 3,5 s. Falta volver a medir en vivo después del push.
  · A un ingeniero en informática el formulario le pedía el registro de la
    Superintendencia de Salud y le daba "Kinesióloga" de ejemplo. El registro
    solo aparece en rubros de salud (y se limpia en el servidor si no aplica);
    los ejemplos de título e institución cambian según el grupo del rubro.
    El CV reconoce desarrollo web.
---

---
[18-10-2026, noche] — Diego: "no sé cómo agregar fotos para mostrar mis trabajos,
la única foto es el logo" y "siento que hay mucho espacio vacío en la web".
  · La ficha decía "Todavía no subes fotos. Agregar fotos →" y el formulario no
    tenía dónde: solo el logo. Nueva sección "Fotos de tus trabajos" al crear y
    al editar: hasta 8, WebP 1024 px <100 KB sin EXIF (procesar_foto ganó el
    parámetro lado_maximo), cada una con "Portada" y "Quitar". Quitar borra el
    archivo (no deja huérfanos en R2); si se quita la portada, pasa a la
    siguiente. Los ids que llegan del formulario se buscan SOLO dentro del
    perfil propio (G-02): una prueba con mutación lo comprueba.
  · El aviso de la ficha ahora lleva directo a #fotos.
  · Formulario en dos columnas (7/5, 8/4 en xl): a la derecha, fija al hacer
    scroll, la tarjeta tal como la verá un cliente, al día con lo que se escribe
    (nombre, rubro, comuna, descripción, logo, portada, modalidades) y tres
    consejos. En el celular no se muestra. Las fotos nuevas se previsualizan
    antes de subirlas y avisa si pasan de 8.
  · Verificado con Playwright en un servidor local (SQLite): escritorio y
    celular sin errores JS ni scroll horizontal; envío real con una foto nueva y
    cambio de portada, la ficha mostró las 3. Usuario de prueba borrado.
Pruebas: 230.
---
