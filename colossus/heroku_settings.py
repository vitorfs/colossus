# flake8: noqa

from .production_settings import *

# Insert WhiteNoise middleware after SecurityMiddleware
security_middleware_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(security_middleware_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
