from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Sighting(models.Model):
    location_name = models.CharField(max_length=200)
    location_point = models.PointField(srid=4326, help_text="Location coordinates (EPSG:4326 - WGS84)")
    description = models.TextField(blank=True)
    sighted_by = models.CharField(max_length=255)
    sighted_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("location_name", heading="Location"),
        FieldPanel("location_point", heading="Coordinates"),
        FieldPanel("description"),
        FieldPanel("sighted_by", heading="Witnessed by"),
        FieldPanel("sighted_at", heading="Date of sighting"),
    ]

    def __str__(self):
        return f"{self.location_name} - {self.sighted_by}"

    @property
    def latitude(self) -> float | None:
        """Return latitude, handling None values"""
        if self.location_point:
            return float(self.location_point.y)
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude, handling None values"""
        if self.location_point:
            return float(self.location_point.x)
        return None

    @classmethod
    def create_from_coords(cls, name: str, lat: float, lng: float, **kwargs) -> "Sighting":
        """Helper method to create location from lat/lng coordinates"""
        if lat is not None and lng is not None:
            point = Point(float(lng), float(lat), srid=4326)
            return cls.objects.create(name=name, point=point, **kwargs)
        else:
            raise ValueError("Latitude and longitude must not be None")

    def distance_to(self, other_point: Point) -> float | None:
        """Calculate distance to another point (returns distance in meters)"""
        if self.location_point and other_point:
            return self.location_point.distance(other_point)
        return None

    class Meta:
        ordering = ["location_name"]
