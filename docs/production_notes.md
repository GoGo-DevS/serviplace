# SERVIPLACE production notes

Despliegue: Render (plan free, región virginia) + Neon (Postgres, us-east-1)
+ Cloudflare R2 (imágenes) + Cloudflare DNS para serviplace.cl. Todo está en
`render.yaml`; los secretos se pegan a mano en el dashboard de Render.

## Media files

Las imágenes que suben los prestadores van a R2 (bucket `serviplace`,
servido en `https://media.serviplace.cl`). `config/settings.py` exige las 5
variables `R2_*` o ninguna; sin ellas en producción avisa y cae a disco, que
Render borra en cada deploy.

## Datos

El primer deploy carga `directory/fixtures/directorio_inicial.json` (361
prestadores activos, 16 regiones, 346 comunas, 9 categorías) con
`cargar_directorio_inicial`, que solo actúa sobre una base vacía. El respaldo
completo de la base local (460 prestadores, con los ocultos) está fuera del
repo, en `_respaldos-serviplace/serviplace_2026-10-16.json`.

## Admin

Render Free no tiene consola: `asegurar_admin` crea el superusuario en el
build desde `DJANGO_SUPERUSER_*`, solo si no existe. El admin vive en la ruta
de `ADMIN_URL`, nunca en `/admin/`.

## Static files

Static files are collected with `collectstatic` and served by WhiteNoise in production.

## Start command

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```
