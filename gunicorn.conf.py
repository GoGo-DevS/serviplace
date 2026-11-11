"""Configuración de gunicorn (11-11-2026). Gunicorn la lee sola al arrancar
desde esta carpeta, así que vale aunque el startCommand de Render no la nombre.

Por qué existe: guardar un perfil con fotos daba 502. Con el worker "sync" y
30 s de límite, una subida lenta desde un celular (varias fotos de 4-8 MB por
4G) o el procesamiento de las fotos en el plan gratis (una décima de CPU)
pasaban los 30 s: gunicorn mataba el worker y Render respondía 502.

- gthread: mientras un hilo recibe la subida, el worker sigue avisando que está
  vivo, y los demás hilos atienden otras visitas.
- 120 s de límite para lo que de verdad tarda.
"""
import os

workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
worker_class = 'gthread'
threads = 4
timeout = 120
graceful_timeout = 30
keepalive = 5
# Renueva cada worker de vez en cuando: en 512 MB, la memoria que deja Pillow
# no vuelve sola.
max_requests = 500
max_requests_jitter = 50
