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
