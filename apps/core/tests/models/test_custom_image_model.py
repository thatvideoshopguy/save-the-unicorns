from django.test import TestCase
from wagtail.images.tests.utils import get_test_image_file

from apps.core.models.custom_image_model import CustomImage, CustomRendition


class CustomImageModelTestCase(TestCase):
    def setUp(self):
        # Create a test image
        image_file = get_test_image_file()
        self.image = CustomImage.objects.create(
            title="Test Image", file=image_file, alt_text="Custom alt text for testing"
        )
        # Clean up the file reference
        image_file.close()

    def tearDown(self):
        # Clean up any created images
        for image in CustomImage.objects.all():
            if image.file:
                try:
                    image.file.delete(save=False)
                except (OSError, ValueError):
                    pass
        CustomImage.objects.all().delete()

    def test_default_alt_text_with_custom_alt(self):
        """Test default_alt_text returns custom alt_text when available"""
        self.assertEqual(self.image.default_alt_text, "Custom alt text for testing")

    def test_default_alt_text_fallback_to_title(self):
        """Test default_alt_text falls back to title when alt_text is empty"""
        image_file = get_test_image_file()
        image_without_alt = CustomImage.objects.create(
            title="Image Without Alt", file=image_file, alt_text=""
        )
        image_file.close()

        self.assertEqual(image_without_alt.default_alt_text, "Image Without Alt")

    def test_custom_rendition_creation(self):
        """Test that CustomRendition can be created and linked to CustomImage"""

        rendition = self.image.get_rendition("width-100")
        self.assertIsInstance(rendition, CustomRendition)
        self.assertEqual(rendition.image, self.image)

        if rendition.file:
            try:
                rendition.file.delete(save=False)
            except (OSError, ValueError):
                pass
