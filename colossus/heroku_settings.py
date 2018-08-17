# flake8: noqa
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import lazy

from .production_settings import *

# ==============================================================================
# MIDDLEWARE SETTINGS
# ==============================================================================

# Insert WhiteNoise middleware after SecurityMiddleware
security_middleware_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')

MIDDLEWARE.insert(security_middleware_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')


# ==============================================================================
# STATIC FILES SETTINGS
# ==============================================================================

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ==============================================================================
# EMAIL SETTINGS
# ==============================================================================

def heroku_default_email():
    site = get_current_site(request=None)
    from_email = 'noreply@%s' % site.domain
    return from_email

heroku_default_email_lazy = lazy(heroku_default_email)

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=heroku_default_email_lazy())

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('MAILGUN_SMTP_SERVER')

EMAIL_PORT = config('MAILGUN_SMTP_PORT', cast=int)

EMAIL_HOST_USER = config('MAILGUN_SMTP_LOGIN')

EMAIL_HOST_PASSWORD = config('MAILGUN_SMTP_PASSWORD')


# ==============================================================================
# LOGGING SETTINGS
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'testlogger': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}


# ==============================================================================
# THIRD-PARTY APPS SETTINGS
# ==============================================================================

CELERY_BROKER_READ_URL = config('RABBITMQ_BIGWIG_RX_URL')

CELERY_BROKER_WRITE_URL = config('RABBITMQ_BIGWIG_TX_URL')
