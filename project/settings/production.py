# ruff: noqa:F405

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

from .base import *  # noqa:F403

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(" ")

DEBUG = True

# Persistent database connections
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST"),
        "PORT": os.environ.get("DJANGO_DATABASE_PORT"),
        "CONN_MAX_AGE": 60,
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}

# Use cached templates in production
TEMPLATES[0]["APP_DIRS"] = False
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# SSL required for session/CSRF cookies
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Improve password security to a reasonable bare minimum
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Add more raven data to help diagnose bugs
try:
    SENTRY_RELEASE = (Path(BASE_DIR) / Path(".sentry-release")).read_text().strip()
except FileNotFoundError:
    SENTRY_RELEASE = None

sentry_sdk.init(release=SENTRY_RELEASE, integrations=[DjangoIntegration()])

for logger in ["elasticapm.errors", "elasticapm.transport", "elasticapm.transport.http"]:
    ignore_logger(logger)

# Elastic APM
if os.environ.get("ELASTIC_APM_SERVER_URL"):
    INSTALLED_APPS += ["elasticapm.contrib.django.apps.ElasticAPMConfig"]

    MIDDLEWARE = ["elasticapm.contrib.django.middleware.TracingMiddleware", *MIDDLEWARE]

# Cache sessions for optimum performance
if os.environ.get("REDIS_SERVERS"):
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
