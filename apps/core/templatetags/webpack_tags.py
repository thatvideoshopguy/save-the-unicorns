import json
from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()


@register.simple_tag
def webpack_static(asset_name):
    """
    Get the hashed filename from webpack manifest
    Usage: {% webpack_static 'js/app.js' %}
    """

    manifest_path = Path(settings.BASE_DIR, "static", "dist", "manifest.json")

    try:
        with manifest_path.open() as f:
            manifest = json.load(f)

        # Get the hashed filename from manifest
        hashed_filename = manifest.get(asset_name, asset_name)

        return staticfiles_storage.url(hashed_filename)

    except (FileNotFoundError, json.JSONDecodeError):
        return staticfiles_storage.url(asset_name)
