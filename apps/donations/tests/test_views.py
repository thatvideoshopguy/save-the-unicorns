from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.http import Http404

from apps.donations.models import Donation
from apps.donations.views import donation_view


class DonationViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_donation_view_requires_htmx(self):
        """Test that view returns 404 without HTMX header"""
        request = self.factory.get("/")
        with self.assertRaises(Http404):
            donation_view(request)

    def test_donation_view_with_htmx(self):
        """Test that view works with HTMX header"""
        request = self.factory.get("/", HTTP_HX_REQUEST="true")
        response = donation_view(request)
        self.assertEqual(response.status_code, 200)

    def test_donation_post_valid_data(self):
        """Test POST request with valid form data"""
        data = {"name": "Test Donor", "amount": "25.50"}
        request = self.factory.post("/", data, HTTP_HX_REQUEST="true")
        response = donation_view(request)
        self.assertEqual(response.status_code, 200)

        # Verify donation was created
        donation = Donation.objects.get(name="Test Donor")
        self.assertEqual(donation.amount, Decimal("25.50"))

    def test_donation_post_invalid_data(self):
        """Test POST request with invalid form data"""
        data = {"name": "", "amount": "0.00"}
        request = self.factory.post("/", data, HTTP_HX_REQUEST="true")
        response = donation_view(request)
        self.assertEqual(response.status_code, 200)

        # Verify no donation was created
        self.assertEqual(Donation.objects.count(), 0)
