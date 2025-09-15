from django.db import models

from wagtail.images.models import AbstractImage, AbstractRendition, Image


class CustomImage(AbstractImage):
    """
    Custom image model that ensures alt text support.
    """

    alt_text = models.TextField(
        blank=True,
        help_text="Alternative text for screen readers. Leave empty for decorative images.",
    )

    admin_form_fields = (*Image.admin_form_fields, "alt_text")

    # Override the default_alt_text property to use our custom field
    @property
    def default_alt_text(self):
        """Return alt text for use in templates"""
        return self.alt_text or self.title

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"


class CustomRendition(AbstractRendition):
    """
    Custom rendition model to work with our custom image model.
    This is required when using a custom image model.
    """

    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
