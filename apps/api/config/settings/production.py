from .base import *  # noqa: F401, F403
import environ

env = environ.Env()
DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# One JSON object per line, because that is what a log collector can search. A human reading the container
# log still sees the message; a machine can filter by level and request id.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
                      '"message":"%(message)s"}',
        },
    },
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'json'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {'level': 'ERROR', 'handlers': ['console'], 'propagate': False},
        'apps': {'level': 'INFO'},
    },
}


# --- go-live: production images (VibeKaizen) -------------------------------------------------------------
# The live API runs gunicorn behind the web image's Caddy (infra/Dockerfile.api, infra/Dockerfile.web). The
# admin's static files are collected into the image and served by WhiteNoise. Before anything else, the live
# keys are checked by name and the app refuses to start while one is missing or wrong (config/live_env.py,
# deploy/required-env.json). The platform maintains this block.
import os as _os

import environ as _environ

if _os.environ.get('VK_SKIP_LIVE_ENV_CHECK') != '1':  # set only while the image is built
    from config.live_env import enforce as _enforce_live_env
    _enforce_live_env()

_live_env = _environ.Env()
if 'apps.core.health.HealthzMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(0, 'apps.core.health.HealthzMiddleware')
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
                      'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
# TLS ends in front of the app (Render's edge, then Caddy): trust the proxy's X-Forwarded-Proto. The redirect
# is turned off only by the local rehearsal (docker-compose.prod.yml), which has no TLS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = _live_env.bool('SECURE_SSL_REDIRECT', default=True)
# Render names the service's own address; it is always a host this app answers on.
if _os.environ.get('RENDER_EXTERNAL_HOSTNAME') and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, _os.environ['RENDER_EXTERNAL_HOSTNAME']]
