import os

from .base import *  # noqa

DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME", "savetheunicorns_django"),
        "USER": "unicorn_admin",
        "PASSWORD": "3#oD485ewup7",
        "PORT": "5432",
    }
}

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS += ["django_extensions", "wagtail.contrib.styleguide"]

# Webpack runserver
TEMPLATES[0]["OPTIONS"]["context_processors"].append("core.context_processors.browsersync")

# Use vanilla StaticFilesStorage to allow tests to run outside of tox easily
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

SECRET_KEY = "secret"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django debug toolbar - show locally unless DISABLE_TOOLBAR is enabled with environment vars
# eg. DISABLE_TOOLBAR=1 ./manage.py runserver
if not os.environ.get("DISABLE_TOOLBAR"):
    INSTALLED_APPS += ["debug_toolbar"]

    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

# Allow login with remote passwords, but downgrade/swap to crypt for password hashing speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.CryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Disable axes for local usage
AXES_ENABLED = False
