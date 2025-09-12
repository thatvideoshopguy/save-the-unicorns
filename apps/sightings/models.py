# models.py
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Using GeoDjango's PointField instead of separate lat/lng
    point = models.PointField(srid=4326, help_text="Location coordinates (EPSG:4326 - WGS84)")
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("point"),  # GeoDjango admin widget
        FieldPanel("address"),
        FieldPanel("website"),
    ]

    def __str__(self):
        return self.name

    @property
    def latitude(self):
        return self.point.y if self.point else None

    @property
    def longitude(self):
        return self.point.x if self.point else None

    @classmethod
    def create_from_coords(cls, name, lat, lng, **kwargs):
        """Helper method to create location from lat/lng coordinates"""
        point = Point(lng, lat, srid=4326)  # Note: Point takes (x, y) = (lng, lat)
        return cls.objects.create(name=name, point=point, **kwargs)

    def distance_to(self, other_point):
        """Calculate distance to another point (returns distance in meters)"""
        if self.point and other_point:
            return self.point.distance(other_point)
        return None

    class Meta:
        ordering = ["name"]


class MapPage(Page):
    intro = RichTextField(blank=True)
    # Optional: define a bounding box for the map
    map_center = models.PointField(
        srid=4326, default=Point(-4.0, 54.5, srid=4326), help_text="Map center point"  # UK center
    )
    zoom_level = models.IntegerField(default=6, help_text="Initial zoom level")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("map_center"),
        FieldPanel("zoom_level"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        # Get all locations with spatial queries if needed
        locations = Location.objects.all()

        # Optional: Add spatial filtering
        # For example, locations within a certain distance of map center:
        # locations = Location.objects.filter(
        #     point__distance_lte=(self.map_center, D(km=500))
        # )

        context["locations"] = locations
        context["map_center_lat"] = self.map_center.y
        context["map_center_lng"] = self.map_center.x

        return context
