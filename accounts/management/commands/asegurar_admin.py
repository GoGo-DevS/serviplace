"""Crea el superusuario de producción si todavía no existe.

Render Free no tiene consola, así que el admin se crea en el build a partir
de tres variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL y
DJANGO_SUPERUSER_PASSWORD. Solo CREA: si el usuario ya existe no le cambia
la contraseña, para que un deploy no deshaga un cambio hecho desde el admin.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea el superusuario desde variables de entorno, solo si no existe.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()

        if not username or not password:
            self.stdout.write('Sin DJANGO_SUPERUSER_USERNAME/PASSWORD: no se crea admin.')
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'El admin "{username}" ya existe: no se toca.')
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Admin "{username}" creado.'))
