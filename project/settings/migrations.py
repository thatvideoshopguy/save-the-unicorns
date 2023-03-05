from .base import *  # noqa

# makemigrations --check requires a database starting with Wagtail 2.10, but we don't want to try
# connecting to a real one - so use an in-memory sqlite one.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

SECRET_KEY = "secret"
