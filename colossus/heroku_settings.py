# flake8: noqa

from .production_settings import *

# Insert WhiteNoise middleware after SecurityMiddleware
security_middleware_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(security_middleware_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CELERY_BROKER_READ_URL = config('RABBITMQ_BIGWIG_RX_URL')
CELERY_BROKER_WRITE_URL = config('RABBITMQ_BIGWIG_TX_URL')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')


EMAIL_HOST = config('MAILGUN_SMTP_SERVER')
EMAIL_PORT = config('MAILGUN_SMTP_PORT', cast=int)
EMAIL_HOST_USER = config('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = config('MAILGUN_SMTP_PASSWORD')
