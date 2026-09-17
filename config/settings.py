import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

DEFAULT_ALLOWED_HOSTS = '127.0.0.1,localhost,testserver,*'
DEFAULT_FRONTEND_URL = 'http://localhost:5173'


def get_csv_env(name, default):
    return [value.strip() for value in os.getenv(name, default).split(',') if value.strip()]


def get_bool_env(name, default):
    return os.getenv(name, default).lower() in ('true', '1', 't')


SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('DJANGO_SECRET_KEY') or 'dev-only-change-this-secret-key'
DEBUG = get_bool_env('DEBUG', os.getenv('DJANGO_DEBUG', 'True'))
ALLOWED_HOSTS = get_csv_env('DJANGO_ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'bookings',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
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

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'bookings.context_processors.frontend_url',
    ]},
}]

WSGI_APPLICATION = 'config.wsgi.application'

def configure_database():
    database_url = os.getenv('DATABASE_URL', '').strip()
    if database_url:
        ssl_require = 'sslmode=require' in database_url or 'neon.tech' in database_url
        try:
            import dj_database_url
            db_config = dj_database_url.config(
                default=database_url,
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=ssl_require,
            )
            if ssl_require:
                if 'OPTIONS' not in db_config:
                    db_config['OPTIONS'] = {}
                db_config['OPTIONS']['sslmode'] = 'require'
            return db_config
        except ImportError:
            p = urlparse(database_url)
            engine = 'django.db.backends.postgresql'
            if p.scheme.startswith('sqlite'):
                return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': p.path.lstrip('/') or str(BASE_DIR / 'db.sqlite3')}
            elif p.scheme.startswith('mysql'):
                engine = 'django.db.backends.mysql'
            return {
                'ENGINE': engine,
                'NAME': p.path.lstrip('/'),
                'USER': unquote(p.username or ''),
                'PASSWORD': unquote(p.password or ''),
                'HOST': p.hostname or '',
                'PORT': str(p.port or 5432),
                'CONN_MAX_AGE': 600,
            }
    else:
        db_engine = (os.getenv('DB_ENGINE') or 'django.db.backends.postgresql').strip()
        return {
            'ENGINE': db_engine,
            'NAME': (os.getenv('DB_NAME') or 'hoteldb').strip(),
            'USER': (os.getenv('DB_USER') or 'postgres').strip(),
            'PASSWORD': (os.getenv('DB_PASSWORD') or '').strip(),
            'HOST': (os.getenv('DB_HOST') or '127.0.0.1').strip(),
            'PORT': (os.getenv('DB_PORT') or '5432').strip(),
        }

DATABASES = {
    'default': configure_database()
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CORS_ALLOW_ALL_ORIGINS = get_bool_env('CORS_ALLOW_ALL_ORIGINS', 'True')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['*']
CORS_ALLOWED_ORIGINS = get_csv_env(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,https://*.vercel.app,https://*.onrender.com,https://*.railway.app,https://*.koyeb.app',
)

DEFAULT_CSRF_TRUSTED = (
    'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:8000,'
    'https://*.onrender.com,https://*.railway.app,https://*.koyeb.app,https://*.vercel.app'
)
CSRF_TRUSTED_ORIGINS = get_csv_env('CSRF_TRUSTED_ORIGINS', DEFAULT_CSRF_TRUSTED)

FRONTEND_URL = os.getenv('FRONTEND_URL', DEFAULT_FRONTEND_URL)
if FRONTEND_URL and FRONTEND_URL.startswith(('http://', 'https://')):
    clean_fe = FRONTEND_URL.rstrip('/')
    if clean_fe not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(clean_fe)
    if clean_fe not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(clean_fe)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "quickstay-inmemory-cache",
        "TIMEOUT": 600,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser', 'rest_framework.parsers.MultiPartParser', 'rest_framework.parsers.FormParser'],
}

# Kafka Event Streaming Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092')
KAFKA_ENABLED = get_bool_env('KAFKA_ENABLED', 'True')
KAFKA_CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'quickstay-hotel-service')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP', 'quickstay-consumer-group')
KAFKA_TOPIC_PREFIX = os.getenv('KAFKA_TOPIC_PREFIX', 'hotel')

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@quickstay.local')
LOGIN_REDIRECT_URL = '/manage/'
LOGOUT_REDIRECT_URL = FRONTEND_URL
