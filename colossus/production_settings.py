import raven

from .settings import *  # noqa

# ==============================================================================
# CORE SETTINGS
# ==============================================================================

INSTALLED_APPS += [
    'raven.contrib.django.raven_compat',
]


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True


# ==============================================================================
# THIRD-PARTY APPS SETTINGS
# ==============================================================================

RAVEN_CONFIG = {
    'dsn': config('RAVEN_CONFIG_DSN'),
    'release': raven.fetch_git_sha(BASE_DIR),
}
