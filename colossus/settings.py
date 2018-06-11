import os
import string

from django.contrib.messages import constants as messages_constants

from decouple import config, Csv
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADMINS = (
    ('Vitor Freitas', 'vitorfs@gmail.com'),
)

MANAGERS = ADMINS

SECRET_KEY = config('SECRET_KEY', default=string.ascii_letters)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    'debug_toolbar',
    'crispy_forms',

    'colossus.campaigns',
    'colossus.core',
    'colossus.emailtemplates',
    'colossus.lists',
    'colossus.pages',
    'colossus.subscribers',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SITE_ID = 1

ROOT_URLCONF = 'colossus.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'colossus/templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'colossus.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///%s' % os.path.join(BASE_DIR, 'db.sqlite3'))
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')

TIME_ZONE = config('TIME_ZONE', default='UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'colossus/static'),
]

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')

# X_FRAME_OPTIONS = 'DENY'

CSRF_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = not DEBUG

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year

SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG

SECURE_SSL_REDIRECT = not DEBUG

SECURE_BROWSER_XSS_FILTER = not DEBUG

SECURE_CONTENT_TYPE_NOSNIFF = not DEBUG

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = not DEBUG

MESSAGE_TAGS = {
    messages_constants.DEBUG: 'alert-dark',
    messages_constants.INFO: 'alert-primary',
    messages_constants.SUCCESS: 'alert-success',
    messages_constants.WARNING: 'alert-warning',
    messages_constants.ERROR: 'alert-danger',
}

INTERNAL_IPS = [
    '127.0.0.1',
]

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

EMAIL_HOST = config('EMAIL_HOST', default='localhost')

EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='root')

EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)


'''
    First-Party Apps Settings
'''


'''
    Third-Party Apps Settings
'''

DEBUG_TOOLBAR_CONFIG = {
    # 'JQUERY_URL': '',
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'

CELERY_BROKER_URL = 'amqp://localhost'
