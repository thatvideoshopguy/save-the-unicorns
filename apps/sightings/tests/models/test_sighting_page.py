import json
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase, RequestFactory
from wagtail.models import Site

from apps.sightings.models.sighting_model import SightingModel
from apps.sightings.models.sighting_page import SightingPage


class SightingPageTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Get root page and create sighting page
        self.root_page = Site.objects.get(is_default_site=True).root_page

        # Create sighting page with custom map center
        self.sighting_page = SightingPage(
            title="Sightings Map",
            slug="sightings",
            intro="<p>Map of all sightings</p>",
            map_center=Point(-3.0, 55.0, srid=4326),
            zoom_level=8,
        )
        self.root_page.add_child(instance=self.sighting_page)
        self.sighting_page.save_revision().publish()

    def test_sighting_page_creation(self):
        """Test basic sighting page creation and properties"""
        self.assertEqual(self.sighting_page.title, "Sightings Map")
        self.assertEqual(self.sighting_page.template, "sightings/sighting_index.html")
        self.assertEqual(self.sighting_page.zoom_level, 8)
        self.assertIsNotNone(self.sighting_page.map_center)

    @patch("apps.sightings.models.sighting_page.render_to_string")
    def test_get_context_with_sightings(self, mock_render_to_string):
        """Test get_context with sightings that have location points"""
        # Mock the popup HTML rendering
        mock_render_to_string.return_value = (
            '<div class="popup">\nTest content with "quotes"\n</div>'
        )

        # Create test sightings
        sighting1 = SightingModel.objects.create(
            location_name="Location 1",
            location_point=Point(-2.0, 53.0, srid=4326),
            sighted_by="Observer 1",
        )

        sighting2 = SightingModel.objects.create(
            location_name="Location 2",
            location_point=Point(-1.0, 52.0, srid=4326),
            sighted_by="Observer 2",
        )

        request = self.factory.get("/")
        context = self.get_context_for_page(request)

        # Verify context contains expected keys
        self.assertIn("sightings_json", context)
        self.assertIn("map_center_lat", context)
        self.assertIn("map_center_lng", context)

        # Verify map center coordinates
        self.assertEqual(context["map_center_lat"], 55.0)
        self.assertEqual(context["map_center_lng"], -3.0)

        # Verify sightings JSON structure
        sightings_data = json.loads(context["sightings_json"])
        self.assertEqual(len(sightings_data), 2)

        # Check first sighting data
        sighting_data = sightings_data[0]
        self.assertIn("location", sighting_data)
        self.assertIn("lat", sighting_data)
        self.assertIn("lng", sighting_data)
        self.assertIn("popup_html", sighting_data)

        # Verify popup HTML processing (newlines and quotes escaped)
        popup_html = sighting_data["popup_html"]
        self.assertNotIn("\n", popup_html)
        self.assertIn('\\"', popup_html)  # Quotes should be escaped

    def test_get_context_excludes_null_location_points(self):
        """Test that sightings without location points are excluded"""
        SightingModel.objects.create(
            location_name="With Point",
            location_point=Point(-2.0, 53.0, srid=4326),
            sighted_by="Observer 1"
        )

        request = self.factory.get('/')

        with patch('apps.sightings.models.sighting_page.render_to_string') as mock_render:
            mock_render.return_value = '<div>popup</div>'
            context = self.get_context_for_page(request)

        # Should only include sightings with location points (the exclude query works)
        sightings_data = json.loads(context['sightings_json'])
        self.assertEqual(len(sightings_data), 1)
        self.assertEqual(sightings_data[0]['location'], "With Point")

    def test_get_context_with_none_map_center(self):
        """Test get_context when map_center is None"""
        # Create page with None map center by temporarily setting it
        original_center = self.sighting_page.map_center
        self.sighting_page.map_center = None

        request = self.factory.get("/")
        context = self.sighting_page.get_context(request)

        # Restore original center
        self.sighting_page.map_center = original_center

        # Should use default coordinates
        self.assertEqual(context["map_center_lat"], 54.5)
        self.assertEqual(context["map_center_lng"], -4.0)

    @patch("apps.sightings.models.sighting_page.render_to_string")
    def test_popup_html_escaping(self, mock_render_to_string):
        """Test that popup HTML is properly escaped for JSON"""
        # Mock render_to_string to return content with quotes and newlines
        mock_render_to_string.return_value = 'Line 1\nLine 2 with "quoted text" here\n'

        SightingModel.objects.create(
            location_name="Test Location",
            location_point=Point(-2.0, 53.0, srid=4326),
            sighted_by="Test Observer",
        )

        request = self.factory.get("/")
        context = self.get_context_for_page(request)

        sightings_data = json.loads(context["sightings_json"])
        popup_html = sightings_data[0]["popup_html"]

        # Verify escaping
        self.assertNotIn("\n", popup_html)  # Newlines removed
        self.assertIn('\\"', popup_html)  # Quotes escaped
        self.assertEqual(popup_html, 'Line 1Line 2 with \\"quoted text\\" here')

    def test_get_context_empty_sightings(self):
        """Test get_context with no sightings"""
        request = self.factory.get("/")
        context = self.get_context_for_page(request)

        # Should have empty sightings array
        sightings_data = json.loads(context["sightings_json"])
        self.assertEqual(len(sightings_data), 0)
        self.assertEqual(sightings_data, [])

    def get_context_for_page(self, request):
        """Helper method to get context from the sighting page"""
        return self.sighting_page.get_context(request)
