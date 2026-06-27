# CLAUDE.md — ServiPlace (directorio/marketplace de servicios locales)
# LEER COMPLETO ANTES DE TOCAR CUALQUIER COSA
# Creado: 26-06-2026 (sesión de análisis + kickoff, GoGoCRM Claude Code)

════════════════════════════════════════════════
## ⚠️ NOTAS CRÍTICAS — LEER PRIMERO
════════════════════════════════════════════════
1. Este proyecto vive en `C:\Users\diego\Documents\serviplace\` — Django, NO está en git todavía.
   Primer commit es tarea #1 de esta sesión.
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
Ubicación: C:\Users\diego\Documents\serviplace
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
| Region               | 1 sola: "Región Metropolitana"                                  |
| Commune               | 1 sola: "Maipú"                                                  |
| Category              | 9: Cerrajería, Gasfitería, Electricidad, Climatización,         |
|                       | Construcción, Limpieza, Jardinería, Carpintería, Pintura        |
| Provider              | 32, TODOS en Maipú (mezcla autorizado/prospecto_publico)         |
| ProviderApplication   | 0 (formulario de postulación gratis, nadie ha postulado aún)     |
| LeadEvent             | tracking de whatsapp_click y detail_view por Provider            |

Hardcode a Maipú detectado en:
- `directory/views.py` → `provider_list`: default `commune_slug = 'maipu'`, título
  "SERVIPLACE Maipú", `og_title` con "Maipú" fijo.
- `directory/views.py` → `whatsapp_redirect`: mensaje "vi tu servicio en SERVIPLACE Maipú".
- `core/views.py` → home/join/about/contact/trust_and_safety: TODOS tienen "Maipú" fijo en
  `page_title`, `meta_description`, `og_title`, `og_description`.
- `core/views.py` → `home`: featured_providers filtrado a `commune__slug='maipu'`.
- `config/settings.py` línea 151: `SITE_DESCRIPTION` menciona "Maipú" fijo.

NO deployado. Sin render.yaml. Sin git. `docs/production_notes.md` ya advierte que media
necesita Cloudinary antes de producción (mismo patrón que GoGoCRM — no reinventar, copiar).

════════════════════════════════════════════════
## LISTA DE PENDIENTES (trabajar en orden)
════════════════════════════════════════════════

🔴 CRÍTICOS — hacer primero:
[ ] git init + primer commit (proyecto entero, sin esto cualquier error es irrecuperable)
[ ] Sacar TODO el hardcode "Maipú" de views.py (core y directory) y settings.py — dejar
    genérico/dinámico según la comuna seleccionada, sin perder SEO local (cada página de
    comuna+categoría debe seguir teniendo su propio title/meta específico, solo que generado
    dinámicamente en vez de fijo).
[ ] Seed de las 16 regiones + ~346 comunas de Chile (dataset estándar INE/SUBDERE) vía
    management command (`seed_regiones_chile` o similar) — idempotente, usar get_or_create.
[ ] Decidir y documentar en DECISIONES TOMADAS: ¿se mantienen los 32 Provider de Maipú como
    están, o se migran de "comuna hardcodeada" a referenciar la Commune real recién seedeada?
    (probablemente ya están bien vinculados a un FK Commune real — verificar, no hay que
    recrearlos).

🟡 IMPORTANTES — expansión nacional:
[ ] Adaptar el patrón de `growth/management/commands/leads_diarios.py` de GoGoCRM (Google
    Maps Places API + filtro) para crear `seed_providers_nacional` — prospección real de
    prestadores por comuna+categoría, no solo Maipú. Empezar por las comunas más grandes
    (Santiago, Puente Alto, Maipú, Las Condes, Viña del Mar, Valparaíso, Concepción,
    La Florida, etc.) antes de cubrir comunas chicas.
[ ] Revisar `directory/forms.py` (ProviderApplicationForm) — confirmar que el formulario de
    postulación gratuita ya no asuma Maipú en ningún lado (mensajes de éxito, etc.).
[ ] Páginas de categoría+comuna indexables individualmente (SEO) — verificar que
    `provider_list` genere URLs y meta tags únicos por combinación real, no solo Maipú.

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

(vacío — primera entrada la escribe la sesión tryhard que arranque el trabajo)
