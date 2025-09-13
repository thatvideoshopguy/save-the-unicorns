from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.template.loader import render_to_string

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from .sighting_model import Sighting


class SightingPage(Page):
    intro = RichTextField(blank=True)
    map_center = models.PointField(
        srid=4326, default=Point(-4.0, 54.5, srid=4326), help_text="Map center point"
    )
    zoom_level = models.IntegerField(default=6, help_text="Initial zoom level")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("map_center"),
        FieldPanel("zoom_level"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        sightings = Sighting.objects.exclude(point__isnull=True)

        sightings_data = []
        for sighting in sightings:
            popup_html = (
                render_to_string(
                    "sightings/includes/leaflet_marker_popup.html", {"sighting": sighting}, request=request
                )
                .replace("\n", "")
                .replace('"', '\\"')
            )

            sightings_data.append(
                {
                    "location": sighting.location_name,
                    "lat": float(sighting.location_point.y),
                    "lng": float(sighting.location_point.x),
                    "popup_html": popup_html,
                }
            )

        context["sightings"] = sightings
        context["map_center_lat"] = float(self.map_center.y) if self.map_center else 54.5
        context["map_center_lng"] = float(self.map_center.x) if self.map_center else -4.0

        return context
