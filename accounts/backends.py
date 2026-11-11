"""Entrar con el nombre de usuario o con el correo (11-11-2026).

Manitos Curiosas no pudo entrar: el login pedía "Nombre de usuario" y la gente
escribe su correo, que es lo que recuerda. Django solo buscaba el usuario
exacto (con mayúsculas incluidas), así que "Manitos" no era "manitos" y un
correo nunca calzaba. Aquí se acepta cualquiera de los dos, sin distinguir
mayúsculas.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class UsuarioOCorreoBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if not username or password is None:
            return None
        texto = username.strip()
        candidatos = get_user_model().objects.filter(Q(username__iexact=texto) | Q(email__iexact=texto))
        # El usuario exacto va primero; un correo puede repetirse entre cuentas
        # (no es único en el registro), así que se prueba la clave en cada una.
        for user in sorted(candidatos, key=lambda u: u.username != texto):
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        if not candidatos:
            # Mismo costo que una clave mala: no se revela si la cuenta existe.
            get_user_model()().set_password(password)
        return None
