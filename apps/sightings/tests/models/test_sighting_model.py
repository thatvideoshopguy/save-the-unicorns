from django.contrib.gis.geos import Point
from django.test import TestCase

from apps.sightings.models.sighting_model import SightingModel


class SightingModelTestCase(TestCase):
    def setUp(self):
        # Create test sightings - all must have location_point due to database constraint
        self.sighting_with_point = SightingModel.objects.create(
            location_name="Test Location",
            location_point=Point(-2.0, 53.0, srid=4326),
            description="A test sighting",
            sighted_by="Test Observer",
        )

        self.sighting_other_point = SightingModel.objects.create(
            location_name="Other Location",
            location_point=Point(-1.0, 52.0, srid=4326),
            description="Another sighting",
            sighted_by="Another Observer",
        )

    def test_str_representation(self):
        """Test the __str__ method"""
        expected = "Test Location - Test Observer"
        self.assertEqual(str(self.sighting_with_point), expected)

    def test_latitude_property_with_point(self):
        """Test latitude property when location_point exists"""
        self.assertEqual(self.sighting_with_point.latitude, 53.0)

    def test_latitude_property_without_point(self):
        """Test latitude property when location_point is None - use mock"""
        # Since we can't create a real instance with None point due to DB constraint,
        # we'll test the property logic by temporarily setting it to None
        original_point = self.sighting_with_point.location_point
        self.sighting_with_point.location_point = None

        result = self.sighting_with_point.latitude

        # Restore original point
        self.sighting_with_point.location_point = original_point

        self.assertIsNone(result)

    def test_longitude_property_with_point(self):
        """Test longitude property when location_point exists"""
        self.assertEqual(self.sighting_with_point.longitude, -2.0)

    def test_longitude_property_without_point(self):
        """Test longitude property when location_point is None - use mock"""
        # Since we can't create a real instance with None point due to DB constraint,
        # we'll test the property logic by temporarily setting it to None
        original_point = self.sighting_with_point.location_point
        self.sighting_with_point.location_point = None

        result = self.sighting_with_point.longitude

        # Restore original point
        self.sighting_with_point.location_point = original_point

        self.assertIsNone(result)

    def test_create_from_coords_success(self):
        """Test create_from_coords with valid coordinates"""
        sighting = SightingModel.create_from_coords(
            name="Coord Location",
            lat=55.0,
            lng=-3.0,
            description="Created from coordinates",
            sighted_by="Coord Observer"
        )

        self.assertEqual(sighting.location_name, "Coord Location")
        self.assertEqual(sighting.latitude, 55.0)
        self.assertEqual(sighting.longitude, -3.0)
        self.assertEqual(sighting.description, "Created from coordinates")
        self.assertEqual(sighting.sighted_by, "Coord Observer")

    def test_create_from_coords_none_lat(self):
        """Test create_from_coords with None latitude"""
        with self.assertRaises(ValueError) as cm:
            SightingModel.create_from_coords(
                name="Invalid Location", lat=None, lng=-3.0, sighted_by="Test"
            )
        self.assertEqual(str(cm.exception), "Latitude and longitude must not be None")

    def test_create_from_coords_none_lng(self):
        """Test create_from_coords with None longitude"""
        with self.assertRaises(ValueError) as cm:
            SightingModel.create_from_coords(
                name="Invalid Location", lat=55.0, lng=None, sighted_by="Test"
            )
        self.assertEqual(str(cm.exception), "Latitude and longitude must not be None")

    def test_create_from_coords_both_none(self):
        """Test create_from_coords with both coordinates None"""
        with self.assertRaises(ValueError) as cm:
            SightingModel.create_from_coords(
                name="Invalid Location", lat=None, lng=None, sighted_by="Test"
            )
        self.assertEqual(str(cm.exception), "Latitude and longitude must not be None")

    def test_distance_to_with_points(self):
        """Test distance_to with both points valid"""
        other_point = Point(-1.0, 52.0, srid=4326)
        distance = self.sighting_with_point.distance_to(other_point)

        # Distance should be a positive float (approximate distance between the points)
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)

    def test_distance_to_with_none_location_point(self):
        """Test distance_to when sighting has no location_point - use mock"""
        other_point = Point(-1.0, 52.0, srid=4326)

        # Test the property logic by temporarily setting location_point to None
        original_point = self.sighting_with_point.location_point
        self.sighting_with_point.location_point = None

        distance = self.sighting_with_point.distance_to(other_point)

        # Restore original point
        self.sighting_with_point.location_point = original_point

        self.assertIsNone(distance)

    def test_distance_to_with_none_other_point(self):
        """Test distance_to with None other_point"""
        distance = self.sighting_with_point.distance_to(None)

        self.assertIsNone(distance)

    def test_distance_to_both_none(self):
        """Test distance_to with both points None - use mock"""
        # Test with temporarily setting location_point to None
        original_point = self.sighting_with_point.location_point
        self.sighting_with_point.location_point = None

        distance = self.sighting_with_point.distance_to(None)

        # Restore original point
        self.sighting_with_point.location_point = original_point

        self.assertIsNone(distance)

    def test_ordering(self):
        """Test that sightings are ordered by location_name"""
        sighting_a = SightingModel.objects.create(
            location_name="A Location",
            location_point=Point(-2.0, 53.0, srid=4326),
            sighted_by="Observer A",
        )
        sighting_z = SightingModel.objects.create(
            location_name="Z Location",
            location_point=Point(-1.0, 52.0, srid=4326),
            sighted_by="Observer Z",
        )

        sightings = list(SightingModel.objects.all())
        # Should be ordered alphabetically by location_name
        location_names = [s.location_name for s in sightings]
        self.assertEqual(location_names, sorted(location_names))
