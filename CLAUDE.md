# CLAUDE.md — ServiPlace (directorio/marketplace de servicios locales)
# LEER COMPLETO ANTES DE TOCAR CUALQUIER COSA
# Creado: 26-06-2026 (sesión de análisis + kickoff, GoGoCRM Claude Code)

════════════════════════════════════════════════
## ⚠️ NOTAS CRÍTICAS — LEER PRIMERO
════════════════════════════════════════════════
1. Este proyecto vive en `C:\Users\diego\Desktop\backup-gogodevs\Proyectos GoGoDevS\GoGoCRM\serviplace\`
   (se movió desde Documents\serviplace). Django, git activo, remote PRIVADO en
   https://github.com/GoGo-DevS/serviplace — subido el 04-09-2026; hasta ese día eran 10 commits
   con los 32 prestadores reales de Maipú en UNA sola copia del disco. El venv es el de GoGoCRM:
   `..\venv\Scripts\python.exe`.
   App `accounts` nueva (autoservicio estilo Yapo). 209 providers en DB (10 comunas).
2. NO está deployado en ningún lado. SQLite local únicamente. Settings ya son
   production-ready (env vars, dj-database-url) pero falta Render+Postgres+Cloudinary.
3. La idea NO es original — existe un competidor real: kalabazaapp.com (ver análisis abajo).
   Esto NO es motivo para frenar — el competidor es débil en sustancia, fuerte solo en marketing.
4. El modelo de datos (Region → Commune → Provider) YA soporta Chile completo sin tocar el
   schema — el problema es que el CÓDIGO (views, templates, settings) está hardcodeado a
   Maipú en todos lados. Sacar ese hardcode es la prioridad #1 técnica.
5. Diego es dueño 100% de este proyecto (no es cliente externo) — "Proyecto propio con
   potencial MUY alto" según sus notas en GoGoCRM. Futuro producto SaaS.
6. Referencia cruzada: GoGoCRM (`C:\Users\diego\Proyectos GoGoDevS\GoGoCRM\`) tiene un
   command `growth/management/commands/leads_diarios.py` que hace prospección automática
   vía Google Maps Places API + filtro IA — es el patrón a adaptar para poblar Providers
   de ServiPlace a nivel nacional (mismo enfoque, otro dominio: prestadores en vez de
   negocios sin web).

════════════════════════════════════════════════
## MODO DE OPERACIÓN
════════════════════════════════════════════════

### 🔥 MODO TRYHARD / AUTÓNOMO (Diego dio luz verde total)
Activación: Diego dice "modo tryhard", "dale duro", "sorpréndeme", o lanza directo con:
```
claude --dangerously-skip-permissions
```

REGLAS MODO TRYHARD:
- Ejecutas TODO sin pedir confirmación en cambios locales/reversibles (código, modelos,
  templates, seeds, migraciones, commits locales).
- SÍ pausas y preguntas antes de: deploy a producción real (Render/dominio), borrar datos
  ya cargados (los 32 Provider de Maipú son reales, no son basura — no resetear sin avisar),
  o cualquier acción que cueste dinero (comprar dominio, upgrade de plan).
- Tomas decisiones de arquitectura por tu cuenta y las documentas en DECISIONES TOMADAS.
- Si algo falla, corriges y sigues — no te quedas paralizado.
- Escribes en BITÁCORA DE SESIÓN cada 30 min o al terminar una tarea de la lista PENDIENTES.
- Al llegar a 15% de contexto: commit, resumen final en bitácora, y te detienes.
- Objetivo explícito de Diego: "que me sorprenda, que me deje una wea de pana" — prioriza
  avance visible y funcional por sobre perfección. Mejor 5 cosas funcionando a medias que
  0 cosas perfectas.

════════════════════════════════════════════════
## ANÁLISIS DE COMPETENCIA — kalabazaapp.com
════════════════════════════════════════════════
Hallazgos (revisado 26-06-2026):
- Se describe como "marketplace de servicios a domicilio en Chile, trabajadores
  verificados y pagos protegidos".
- Categorías mostradas: Electricidad, Gasfitería, Limpieza a domicilio, Maestro.
- Cobertura: dice "Chile" genérico — CERO mención de ciudades/comunas específicas.
- Sin comisión/precio declarado públicamente.
- Sin cantidad de prestadores, sin testimonios, sin casos de éxito.
- Footer dice "© 2026 Kalabaza" — lanzamiento muy reciente, similar antigüedad a ServiPlace.
- Tiene: app móvil (link "/descargar"), programa de referidos, pagos protegidos (feature
  que ServiPlace NO tiene aún — ojo, posible roadmap futuro si el modelo de negocio lo pide).

CONCLUSIÓN ESTRATÉGICA: Kalabaza es fuerte en discurso de marketing (verificación, pagos
seguros) pero no muestra ninguna prueba de tracción real ni presencia local específica.
ServiPlace ya tiene MÁS sustancia funcional hoy (32 Provider reales en Maipú, 10 ya
"autorizado", tracking de views/whatsapp_clicks por prestador, flujo de postulación
gratuito funcionando). La ventaja competitiva real está en:
  1. SEO hiperlocal de verdad — páginas por comuna+categoría indexables, no un "Chile"
     genérico sin contenido específico.
  2. Gratis para prestadores (sin comisión) como gancho de adquisición rápida, mientras
     Kalabaza no aclara su modelo de cobro.
  3. Velocidad de expansión — adaptar el pipeline de prospección de GoGoCRM permite poblar
     decenas de comunas con datos reales mucho más rápido que crecimiento manual.

════════════════════════════════════════════════
## PIVOT DE PRODUCTO — 27-06-2026 (Diego, post-revisión)
════════════════════════════════════════════════
Diego probó la versión nacional y dio feedback directo. 4 cambios de rumbo:

1. **Diseño está muy plano.** Bootstrap genérico sin personalidad. Necesita nivel
   "premium" — cards reales, jerarquía visual, colores/tipografía con identidad propia
   de ServiPlace (no se ve el logo/paleta en ningún lado todavía). Referencia de calidad:
   los sitios que GoGoDevS ya entregó a clientes (ver `C:\Users\diego\Proyectos GoGoDevS\
   GoGoCRM\salon_amanda\` como ejemplo de acabado visual, aunque sea otro rubro).

2. **La estrategia de "pedir permiso antes" NO FUNCIONA — abandonarla.** Diego estuvo
   llamando/escribiendo negocio por negocio pidiendo autorización para usar sus datos
   antes de publicarlos. De ~20 contactados, 2 respondieron. Es lento e ineficiente.
   DECISIÓN: dejar de pedir permiso previo. `seed_providers_nacional` ya scrapea info
   PÚBLICA de Google Maps (nombre, teléfono, categoría, comuna) — eso es suficiente base
   legal para listar (info pública de un negocio público), igual que hace Google Maps,
   Yelp, PáginasAmarillas, etc. El negocio puede reclamar/editar su perfil DESPUÉS de
   publicado (ver punto 3), no antes.

3. **Pivot de modelo: de "directorio curado por Diego" a "estilo Yapo" (autoservicio).**
   La responsabilidad de la veracidad/calidad del contenido recae en CADA USUARIO, no en
   Diego como curador. Esto significa:
   - Cualquier persona puede crear una cuenta y publicar su propio servicio directamente
     (sin moderación previa tipo `ProviderApplication` actual — ese flujo de aprobación
     manual es DEMASIADO LENTO para escalar a nivel nacional).
   - `Provider` necesita un campo `owner` (FK a `User`, nullable — los scrapeados de
     Google Maps no tienen owner hasta que alguien los reclama; los creados por
     autoservicio sí tienen owner desde el día 1).
   - Flujo de "reclamar perfil": si tu negocio ya aparece scrapeado, puedes reclamarlo
     (verificación simple, ej. código por WhatsApp al número listado) y pasa a ser tuyo.
   - Página de Términos/Responsabilidad clara: "ServiPlace es una vitrina, cada usuario es
     responsable de la veracidad de su información" — estilo Yapo/Marketplace, no estilo
     directorio editorial.

4. **Monetización futura (NO implementar pagos reales todavía, solo dejar la estructura
   lista):** el negocio real eventual es cobrar suscripción a prestadores por un perfil
   "verificado" (destacado, más visible, badge de confianza). Por ahora:
   - Mantener/extender `is_verified` e `is_featured` (ya existen) como los campos que
     eventualmente se activan vía pago.
   - NO integrar una pasarela de pago real sin que Diego elija el proveedor explícitamente
     (Webpay/Flow/Mercado Pago) — eso es decisión de negocio, no técnica. Solo dejar el
     modelo/campos listos (ej. `subscription_status`, `subscription_expires_at` si aplica)
     y una página "Hazte Verificado" que por ahora derive a WhatsApp manual (como hace
     GoGoCRM con sus propuestas — cobro manual mientras no hay volumen para justificar
     una pasarela automatizada).

5. **Sobre "que se haga viral":** el código puede construir los MECANISMOS de crecimiento
   (botón compartir por WhatsApp en cada perfil, links con buenas previews OG, programa de
   referidos simple, páginas SEO ya cubiertas). Lo que el código NO puede garantizar es que
   alguien lo comparta o se vuelva viral de verdad — esa parte depende de que Diego lo
   promocione (grupos de Facebook de Maipú/comunas, redes, etc.) una vez esté listo. Ser
   honesto con Diego sobre esto en cualquier resumen de sesión.

════════════════════════════════════════════════
## REGLAS DE ORO (nunca violar)
════════════════════════════════════════════════
1. Leer este archivo completo antes de cualquier acción.
2. NUNCA borrar los 32 Provider de Maipú existentes sin respaldo (son datos reales,
   algunos "autorizado" = verificados de verdad).
3. Código siempre completo — sin placeholders ni "completa esto tú".
4. Migraciones de Django: nunca editar una ya aplicada, siempre crear una nueva.
5. Si algo falla, corregir y seguir — no quedarse paralizado.
6. Commitear a git al final de CADA sesión (este proyecto recién empieza a usar git).
7. Al tomar decisión de arquitectura → documentar en DECISIONES TOMADAS.
8. Escribir en BITÁCORA cada 30 min o al terminar tarea importante.
9. Antes de deployar o gastar dinero (dominio, upgrade Render/Cloudinary) → confirmar con Diego.

════════════════════════════════════════════════
## CONTEXTO DEL PROYECTO
════════════════════════════════════════════════
Proyecto: ServiPlace — Directorio/marketplace de servicios locales en Chile
Desarrollador: Diego Dinamarca (fundador GoGoDevS)
Ubicación: C:\Users\diego\Desktop\backup-gogodevs\Proyectos GoGoDevS\GoGoCRM\serviplace
Repo: https://github.com/GoGo-DevS/serviplace (privado, desde 04-09-2026)
Dominio objetivo: serviplace.cl
Stack: Django 5.2 + PostgreSQL (prod) / SQLite (local) + Render + Cloudflare + WhiteNoise
Visión: piloto inicial pensado en Ciudad de los Valles / Maipú (notas de GoGoCRM), pero
  Diego decidió ahora (26-06-2026): **ir directo a cobertura nacional**, no piloto acotado.

════════════════════════════════════════════════
## ESTADO REAL (auditado 26-06-2026)
════════════════════════════════════════════════
Apps: `core` (páginas institucionales), `directory` (el directorio en sí), `leads` (tracking
de eventos WhatsApp/vistas).

| Modelo               | Estado                                                          |
|----------------------|------------------------------------------------------------------|
| Region               | 16 (Chile completo, INE/SUBDERE) — seedeado 26-06-2026          |
| Commune               | 346 (Chile completo) — seedeado 26-06-2026                       |
| Category              | 9: Cerrajería, Gasfitería, Electricidad, Climatización,         |
|                       | Construcción, Limpieza, Jardinería, Carpintería, Pintura        |
| Provider              | 32, TODOS en Maipú/RM (mezcla autorizado/prospecto_publico)      |
| ProviderApplication   | 0 (formulario de postulación gratis, nadie ha postulado aún)     |
| LeadEvent             | tracking de whatsapp_click y detail_view por Provider            |

Hardcode a Maipú: ELIMINADO en sesión 26-06-2026.
- `directory/views.py`, `core/views.py`, `config/settings.py`, `directory/forms.py`: limpio.
- Los 32 Provider de Maipú siguen intactos; FK commune→region correcta (RM).

Git: inicializado. 2 commits. NO deployado. Sin render.yaml. `docs/production_notes.md`
ya advierte que media necesita Cloudinary antes de producción.

════════════════════════════════════════════════
## LISTA DE PENDIENTES (trabajar en orden)
════════════════════════════════════════════════

🔴 CRÍTICOS — hacer primero:
[x] git init + primer commit (commit 1cabed9, 26-06-2026)
[x] Sacar TODO el hardcode "Maipú" — views.py, settings.py, forms.py. SEO dinámico OK.
[x] Seed 16 regiones + 346 comunas de Chile (seed_regiones_chile, 26-06-2026).
[x] Decisión documentada: 32 Providers conservados, FK commune→RM corregida. No recrear.

🟡 IMPORTANTES — expansión nacional:
[ ] Adaptar el patrón de `growth/management/commands/leads_diarios.py` de GoGoCRM (Google
    Maps Places API + filtro) para crear `seed_providers_nacional` — prospección real de
    prestadores por comuna+categoría, no solo Maipú. Empezar por las comunas más grandes
    (Santiago, Puente Alto, Maipú, Las Condes, Viña del Mar, Valparaíso, Concepción,
    La Florida, etc.) antes de cubrir comunas chicas.
[x] Templates: cero hardcode "Maipú" en todos los templates (base, home, join, about,
    contact, trust_and_safety, provider_list, provider_detail, _provider_card).
[x] Dropdown comunas: ahora tiene optgroup por región (16 grupos, 346 comunas) + opción
    "Todas" al tope. UI completamente usable.
[x] sitemap.xml: 4 sitemaps (estáticas, providers, comunas, categoria×comuna).
    URLs SEO hiperlocales generadas automáticamente por cada (cat, commune) con providers.
[x] render.yaml: plan free, Neon DB, Cloudinary, Google Maps API — listo para deploy.
[x] requirements.txt: cloudinary + django-cloudinary-storage añadidos.
[x] build.sh: incluye seed_regiones_chile — 346 comunas disponibles desde primer deploy.
[x] settings.py: GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_REGION=CL, Cloudinary condicional.

🔵 PIVOT 27-06-2026 — COMPLETADO en sesión 27-06-2026:
[x] Rediseño visual completo — Space Grotesk + Plus Jakarta Sans, paleta índigo/esmeralda,
    provider cards con accent bar + avatar letra, hero con stats card, toast messages.
[x] seed_providers_offline: 177 providers sintéticos en 10 comunas grandes (sin API key).
    PENDIENTE: cuando Diego tenga GOOGLE_MAPS_API_KEY, correr seed_providers_nacional real.
[x] Modelo autoservicio estilo Yapo:
    - Provider.owner (FK User, null=True) + claimed_at + subscription_status/expires_at.
    - App `accounts`: registro, login, logout, dashboard, publicar, editar, reclamar perfil.
    - UserProfile con referral_code único para programa de referidos.
    - Página Términos de Uso (responsabilidad en usuario, modelo Yapo).
[x] Scaffolding monetización: subscription_status/expires_at en Provider,
    página "Hazte Verificado" → WhatsApp manual, badge en cards y detail.
[x] Mecanismos de crecimiento: compartir WhatsApp en detail, copiar enlace,
    OG tags completos (og:image/url/description), referral links con ?ref=CODE.

⏸️ PENDIENTE (próxima sesión):
[ ] Reemplazar seed offline por datos reales de Google Maps (cuando Diego tenga API key).
    Comando listo: `python manage.py seed_providers_nacional`.
[ ] Subir imágenes de portada para los providers (Cloudinary ya configurado).
[ ] Deploy a Render (espera confirmación de Diego — ver sección confirmación).

⏸️ REQUIERE CONFIRMACIÓN DE DIEGO antes de proceder:
[ ] Crear cuenta Neon (DB Postgres) y copiar DATABASE_URL.
[ ] Crear cuenta Cloudinary y copiar CLOUDINARY_URL.
[ ] Conectar repo a Render (New > Blueprint > render.yaml).
[ ] Configurar dominio serviplace.cl en Cloudflare.
[ ] (Opcional) GitHub Action para correr seed_providers_nacional automáticamente.

🟢 DEPLOY — al final, con confirmación de Diego antes de gastar:
[ ] render.yaml (copiar patrón exacto de GoGoCRM: web service plan free + Postgres vía Neon
    + CLOUDINARY_URL desde el día 1, no después — ya sufrimos ese error en GoGoCRM, no
    repetirlo aquí).
[ ] Confirmar con Diego antes de comprar/configurar dominio serviplace.cl.

════════════════════════════════════════════════
## DECISIONES TOMADAS
════════════════════════════════════════════════
[26-06-2026] Diego decide: NO hacer piloto acotado (Ciudad de los Valles → Maipú → Chile).
  Ir directo a cobertura nacional desde el inicio del rework.
[26-06-2026] Cloudinary se configura en el render.yaml DESDE EL PRIMER DEPLOY, no se agrega
  después (lección aprendida en GoGoCRM: migrar imágenes ya subidas es trabajo extra evitable).
[26-06-2026] Los 32 Provider de Maipú se mantienen AS-IS. Su FK commune ya apuntaba a la
  Commune "Maipú" real — solo se corrigió el FK commune.region a "Región Metropolitana de
  Santiago". No se recrearon ni se borraron datos.
[26-06-2026] seed_regiones_chile.py usa get_or_create por slug de comuna (no por nombre)
  para ser resiliente a tildes y variantes tipográficas. El slug es la clave canónica.

════════════════════════════════════════════════
## RUTINA DE ARRANQUE
════════════════════════════════════════════════
Al iniciar SIEMPRE ejecutar en orden:
1. Leer este CLAUDE.md completo
2. python manage.py check
3. python manage.py showmigrations
4. git status (una vez exista el repo)
5. Revisar último bloque de BITÁCORA DE SESIÓN
6. Si modo tryhard: comenzar con primer pendiente 🔴 sin esperar confirmación

════════════════════════════════════════════════
## BITÁCORA DE SESIÓN
════════════════════════════════════════════════
INSTRUCCIÓN: escribir entrada cada 30 min O al terminar tarea.
Formato obligatorio:

---
[FECHA] [HORA] — Modo: tryhard/colaborativo
Tarea completada:
Archivos modificados:
Decisiones tomadas:
Bugs encontrados/resueltos:
Próxima tarea:
---

---
[26-06-2026] 00:00 — Modo: tryhard
Tarea completada: Las 3 tareas 🔴 CRÍTICAS en orden.
  1. git init + .gitignore + .gitattributes (LF) + primer commit (58 archivos).
  2. Hardcode "Maipú" eliminado: directory/views.py (3 puntos), core/views.py (5 vistas),
     config/settings.py (SITE_NAME/SITE_DESCRIPTION), directory/forms.py (labels+placeholders).
     Django check limpio post-cambios. provider_list ahora muestra Chile completo sin filtro.
  3. seed_regiones_chile: 16 regiones + 346 comunas INE/SUBDERE. Idempotente (get_or_create
     por slug). Antigua "Región Metropolitana" huérfana eliminada. 32 providers intactos.
Archivos modificados: directory/views.py, core/views.py, config/settings.py,
  directory/forms.py, CLAUDE.md + nuevo: .gitignore, .gitattributes,
  directory/management/commands/seed_regiones_chile.py
Decisiones tomadas: 32 providers conservados. FK region corregida automáticamente por seed.
Bugs encontrados/resueltos: Región duplicada ("RM" vs "RM de Santiago") — eliminada la vieja.
Próxima tarea: 🟡 seed_providers_nacional (adaptar leads_diarios.py de GoGoCRM).
---
[26-06-2026] 01:00 — Modo: tryhard (continuación)
Tarea completada: Tareas 🟡 iniciadas.
  - seed_providers_nacional.py: command completo, Google Maps Places API inline.
    Top 20 comunas × todas las categorías. --dry-run, --comunas, --categorias, --max-per-query.
    Requiere GOOGLE_MAPS_API_KEY en env. Dedup por business_name+commune.
  - Templates: 100% sin hardcode. Todas las views funcionales verificadas con test client.
  - Dropdown comunas: optgroup por región. 346 comunas en 16 grupos + opción "Todas".
Archivos modificados: directory/views.py (Prefetch regions), todos los templates HTML,
  + nuevo: directory/management/commands/seed_providers_nacional.py
Decisiones tomadas: Ninguna nueva.
Bugs encontrados/resueltos: Assertion test erróneo (Maipú en datos de provider es correcto).
Próxima tarea: sitemap.xml SEO + render.yaml (requiere confirmación Diego para deploy).
---
[27-06-2026] 02:00 — Modo: tryhard (cierre de sesión)
Tarea completada: TODAS las tareas 🔴 y 🟡 críticas + render.yaml listo.
  - sitemap.xml: 4 sitemaps, genera URLs SEO hiperlocales automáticamente.
  - render.yaml + Cloudinary + Google Maps API en settings.
  - build.sh incluye seed_regiones_chile para deploy limpio a Postgres.
  - 6 commits totales en esta sesión.
Archivos modificados: config/settings.py, requirements.txt, build.sh, render.yaml,
  core/sitemaps.py, core/views.py, directory/views.py, todos los templates HTML.
Decisiones tomadas: render.yaml listo pero SIN deployar — espera confirmación Diego.
Bugs encontrados/resueltos: Región RM duplicada del seed antiguo → eliminada.
Próxima tarea: Deploy (con Diego). Luego: seed_providers_nacional con API key real.
---

---
[27-06-2026] 01:00 — Modo: tryhard (sesión nocturna — pivot completo)
Tarea completada: TODAS las tareas 🔵 PIVOT completadas en una sola sesión.

1. REDISEÑO VISUAL v3:
   - Fuentes: Space Grotesk (headings) + Plus Jakarta Sans (body) — personalidad real.
   - Paleta: índigo profundo (#1a4fd6) + verde esmeralda (#059669).
   - Provider cards: accent bar superior (azul/verde/ámbar según estado), avatar letra,
     layout con header+tags+desc+actions bien jerarquizado.
   - Hero: stats card animada a la derecha, eyebrow con punto verde pulsante.
   - Toast messages: slide-in desde derecha, auto-dismiss 4.5s.
   - Contact card sidebar: header gradiente azul, CTA verde prominente.
   - Share row en detail: WhatsApp + copiar enlace.
   - Join band: gradiente azul con decoración geométrica, call-to-action fuerte.

2. CONTENIDO (sin Google Maps API):
   - seed_providers_offline: 177 providers ficticios pero plausibles en 10 comunas.
     Total BD: 209 providers, 10 comunas activas.
   - Emojis en categorías: cerrajería, gasfitería, electricidad, etc.

3. MODELO AUTOSERVICIO (estilo Yapo):
   - Provider.owner (FK User, null) + subscription_status + claimed_at.
   - App accounts: UserProfile (referral_code único auto-generado).
   - Flujos: registro, login, logout, dashboard, publicar, editar, reclamar perfil.
   - Sin moderación previa — publica de inmediato.
   - Términos de Uso: responsabilidad en el usuario publicante.

4. MONETIZACIÓN (scaffolding):
   - subscription_status/expires_at en Provider.
   - Página "Hazte Verificado" → WhatsApp manual.
   - Badge en cards y detail page para promover verificación.

5. CRECIMIENTO:
   - Compartir por WhatsApp desde cualquier provider detail.
   - Copiar enlace directo.
   - OG tags completos: og:title, og:description, og:image, og:url, twitter:card.
   - Programa de referidos: ?ref=CODE en registro, UserProfile.referred_by.
   - Referral link en dashboard de cada usuario.

Archivos modificados: 31 archivos, 2344 inserciones, 1057 eliminaciones.
Commit: 41e3d61 feat: pivot Yapo — autoservicio, rediseno visual v3, seed 177 providers

Bugs encontrados/resueltos:
  - |default:meta_description sin comillas → VariableDoesNotExist. Fix: {% firstof %}.
  - Emojis en Windows cp1252 → usar unicode escapes en Python inline.

Decisiones tomadas:
  - Provider.owner SET_NULL (no CASCADE) — si el usuario se borra, el perfil sobrevive.
  - Seed offline sintético es suficiente para demostración; datos reales vía Google Maps
    cuando Diego active la API key.
  - UserProfile se crea vía signal post_save en User — transparente.

Próxima tarea:
  - Deploy a Render (requiere confirmación Diego).
  - Cuando haya API key: correr seed_providers_nacional con comunas reales.
  - Subir fotos de portada a algunos providers para ver cards con imágenes.
---
