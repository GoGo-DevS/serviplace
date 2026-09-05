"""
Settings de ServiPlace.

Local: SQLite, DEBUG=True, media en disco.
Render: RENDER=true → DEBUG=False, Postgres por DATABASE_URL (Neon), media en
Cloudflare R2 (5 variables, guarda que falla cerrada), WhiteNoise para estáticos.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# .env local (nunca se commitea). En Render las variables vienen del dashboard.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:  # pragma: no cover
    pass


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=''):
    raw_value = os.environ.get(name, default)
    return [item.strip() for item in raw_value.split(',') if item.strip()]


ON_RENDER = env_bool('RENDER', default=False)
DEBUG = env_bool('DEBUG', default=not ON_RENDER)

SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Falta SECRET_KEY en producción.')
    SECRET_KEY = 'django-insecure-solo-desarrollo-local-n9ucxwi$)yvn2bv71486l'

# Hosts: cerrado. En Render se agrega solo el hostname del servicio; el dominio
# propio (serviplace.cl) va en ALLOWED_HOSTS del dashboard.
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver' if DEBUG else '')
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS vacío en producción: pon el dominio en la variable ALLOWED_HOSTS.')

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
for host in ALLOWED_HOSTS:
    if host not in ('127.0.0.1', 'localhost', 'testserver') and f'https://{host}' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')

# El admin de Django no vive en /admin/ en producción: ruta secreta por variable.
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/' if DEBUG else '').strip('/')
ADMIN_ENABLED = bool(ADMIN_URL)
ADMIN_URL = f'{ADMIN_URL}/' if ADMIN_URL else ''

# URL pública canónica (para sitemap, og:url, schema). Sin esquema al final.
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/') or (
    f'https://{RENDER_EXTERNAL_HOSTNAME}' if RENDER_EXTERNAL_HOSTNAME else 'http://127.0.0.1:8000'
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'core',
    'directory',
    'leads',
    'accounts',
]

LOGIN_URL = '/cuenta/login/'
LOGIN_REDIRECT_URL = '/cuenta/dashboard/'
LOGOUT_REDIRECT_URL = '/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.sitio',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

DATABASE_URL = os.environ.get('DATABASE_URL')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if DATABASE_URL:
    import dj_database_url
    # conn_max_age=0: Neon suspende el compute solo sin conexiones abiertas. Con 600 una
    # conexión viva + un monitor cada 5 min = 24 h facturadas por día (pasó en Punto Parcelas).
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=0, conn_health_checks=True)
elif not DEBUG:
    raise ImproperlyConfigured('Producción sin DATABASE_URL: SQLite en Render se borra en cada deploy.')


# Password validation — mínimo 8, no común, no numérica, no parecida al usuario.

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Freno de fuerza bruta en el login (ver accounts.views.LoginThrottledView).
LOGIN_MAX_INTENTOS = int(os.environ.get('LOGIN_MAX_INTENTOS', '8'))
LOGIN_VENTANA_MINUTOS = int(os.environ.get('LOGIN_VENTANA_MINUTOS', '15'))

# Límites por IP en formularios públicos (filas creadas en la ventana).
LIMITE_REGISTROS_POR_IP = (3, 60)     # 3 cuentas por hora
LIMITE_PERFILES_POR_IP = (5, 60)      # 5 perfiles por hora
LIMITE_REPORTES_POR_IP = (6, 60)      # 6 reportes por hora


# Internationalization

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        )
    },
}

# ── Imágenes subidas: Cloudflare R2 desde el día uno (regla 12 de GoGoDevS) ──
# Render borra el disco en cada deploy. R2 no cobra egreso (10 GB gratis).
# Cloudinary cobra por SERVIR y ya se pasó de cupo dos veces con otros clientes.
# La guarda exige las CINCO variables: con 2 de 5 el sitio arrancaría sirviendo
# fotos rotas (pasó con Popi el 14-08-2026). Sin ninguna, cae a disco AVISANDO.
R2_VARS = ('R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET', 'R2_ENDPOINT', 'R2_PUBLIC_URL')
_r2 = {name: os.environ.get(name, '').strip() for name in R2_VARS}
_r2_presentes = [name for name, value in _r2.items() if value]
USE_R2 = len(_r2_presentes) == len(R2_VARS)

if _r2_presentes and not USE_R2:
    faltan = [name for name in R2_VARS if name not in _r2_presentes]
    raise ImproperlyConfigured(
        f'R2 a medias: faltan {", ".join(faltan)}. Con R2 incompleto el sitio serviría imágenes rotas. '
        f'Pon las cinco o ninguna.'
    )

if USE_R2:
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'access_key': _r2['R2_ACCESS_KEY_ID'],
            'secret_key': _r2['R2_SECRET_ACCESS_KEY'],
            'bucket_name': _r2['R2_BUCKET'],
            'endpoint_url': _r2['R2_ENDPOINT'],
            'region_name': 'auto',       # R2 no usa regiones, boto3 exige una
            'querystring_auth': False,   # URLs públicas sin firma ni vencimiento
            'default_acl': None,         # R2 no implementa ACL de S3
            'file_overwrite': False,
            'custom_domain': _r2['R2_PUBLIC_URL'].replace('https://', '').replace('http://', '').rstrip('/'),
        },
    }
elif not DEBUG:
    import warnings
    warnings.warn(
        'ServiPlace en producción SIN R2: las imágenes van a disco y se borran en el próximo deploy. '
        'Configura las 5 variables R2_*.',
        RuntimeWarning,
    )


# ── Seguridad en producción ──────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # el JS del sitio no lo lee, pero Django lo necesita para forms
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 días; subir a 1 año cuando el dominio esté estable
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False


# ── Sitio ────────────────────────────────────────────────────────────────────
SITE_NAME = 'ServiPlace'
SITE_DESCRIPTION = 'Encuentra gásfiter, cerrajero, electricista y otros servicios en tu comuna. Contacto directo por WhatsApp, sin comisión.'
DEFAULT_CONTACT_WHATSAPP = os.environ.get('DEFAULT_CONTACT_WHATSAPP', '')
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'contacto@serviplace.cl')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
GOOGLE_MAPS_REGION = 'CL'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO' if not DEBUG else 'WARNING'},
}
