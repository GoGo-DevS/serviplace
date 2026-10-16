#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py cargar_directorio_inicial   # solo en base vacía: nunca pisa datos de producción
python manage.py seed_regiones_chile         # idempotente: 16 regiones + 346 comunas
python manage.py asegurar_admin              # crea el admin desde variables, solo si no existe
