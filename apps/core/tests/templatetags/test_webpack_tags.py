import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.core.templatetags.webpack_tags import webpack_static


class WebpackTagsTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manifest_path = Path(self.test_dir, "static", "dist", "manifest.json")
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    @override_settings(BASE_DIR=None)
    def test_webpack_static_with_valid_manifest(self):
        """Test webpack_static returns hashed filename from manifest"""
        manifest_data = {"js/app.js": "js/app.abc123.js", "css/style.css": "css/style.def456.css"}

        with patch("apps.core.templatetags.webpack_tags.settings") as mock_settings:
            mock_settings.BASE_DIR = self.test_dir

            # Write manifest file
            with open(self.manifest_path, "w") as f:
                json.dump(manifest_data, f)

            with patch("apps.core.templatetags.webpack_tags.staticfiles_storage") as mock_storage:
                mock_storage.url.return_value = "/static/js/app.abc123.js"

                result = webpack_static("js/app.js")
                mock_storage.url.assert_called_with("js/app.abc123.js")
                self.assertEqual(result, "/static/js/app.abc123.js")

    @override_settings(BASE_DIR=None)
    def test_webpack_static_asset_not_in_manifest(self):
        """Test webpack_static returns original filename when asset not in manifest"""
        manifest_data = {"other/file.js": "other/file.xyz789.js"}

        with patch("apps.core.templatetags.webpack_tags.settings") as mock_settings:
            mock_settings.BASE_DIR = self.test_dir

            # Write manifest file
            with open(self.manifest_path, "w") as f:
                json.dump(manifest_data, f)

            with patch("apps.core.templatetags.webpack_tags.staticfiles_storage") as mock_storage:
                mock_storage.url.return_value = "/static/js/missing.js"

                result = webpack_static("js/missing.js")
                mock_storage.url.assert_called_with("js/missing.js")
                self.assertEqual(result, "/static/js/missing.js")

    @override_settings(BASE_DIR=None)
    def test_webpack_static_file_not_found(self):
        """Test webpack_static handles FileNotFoundError gracefully"""
        with patch("apps.core.templatetags.webpack_tags.settings") as mock_settings:
            mock_settings.BASE_DIR = self.test_dir
            # Don't create the manifest file - this will cause FileNotFoundError

            with patch("apps.core.templatetags.webpack_tags.staticfiles_storage") as mock_storage:
                mock_storage.url.return_value = "/static/js/app.js"

                result = webpack_static("js/app.js")
                mock_storage.url.assert_called_with("js/app.js")
                self.assertEqual(result, "/static/js/app.js")

    @override_settings(BASE_DIR=None)
    def test_webpack_static_invalid_json(self):
        """Test webpack_static handles invalid JSON gracefully"""
        with patch("apps.core.templatetags.webpack_tags.settings") as mock_settings:
            mock_settings.BASE_DIR = self.test_dir

            # Write invalid JSON
            with open(self.manifest_path, "w") as f:
                f.write("invalid json content")

            with patch("apps.core.templatetags.webpack_tags.staticfiles_storage") as mock_storage:
                mock_storage.url.return_value = "/static/js/app.js"

                result = webpack_static("js/app.js")
                mock_storage.url.assert_called_with("js/app.js")
                self.assertEqual(result, "/static/js/app.js")
