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
