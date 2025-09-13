# ruff: noqa:F405
import os
import sys

from .base import *  # noqa:F403

DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME"),
        "USER": os.environ.get("DJANGO_DATABASE_USERNAME"),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD"),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST"),
        "PORT": os.environ.get("DJANGO_DATABASE_PORT"),
    }
}

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS += ["django_extensions"]

# Webpack runserver
TEMPLATES[0]["OPTIONS"]["context_processors"].append("core.context_processors.browsersync")

# Use vanilla StaticFilesStorage to allow tests to run outside of tox easily
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

SECRET_KEY = "secret"  # noqa:S105

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django debug toolbar - show locally unless DISABLE_TOOLBAR is enabled with environment vars
# eg. DISABLE_TOOLBAR=1 ./manage.py runserver
if not os.environ.get("DISABLE_TOOLBAR") and "test" not in sys.argv:
    INSTALLED_APPS += ["debug_toolbar"]

    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]

    DEBUG_TOOLBAR_CONFIG = {
        "SKIP_TEMPLATE_PREFIXES": ("django/forms/widgets/", "admin/widgets/", "bootstrap/"),
        "RESULTS_CACHE_SIZE": 200,
        # Ignore callback for HTMX requests and Wagtail Admin
        "SHOW_TOOLBAR_CALLBACK": lambda request: (
            False
            if (request.headers.get("HX-Request") or request.path.startswith("/admin/"))
            else True
        ),
    }

# Allow login with remote passwords, but downgrade/swap for faster password hashing speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Disable axes for local usage
AXES_ENABLED = False
