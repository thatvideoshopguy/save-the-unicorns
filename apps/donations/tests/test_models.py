from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.donations.models import Donation


class DonationModelTestCase(TestCase):
    def test_create(self):
        """Test basic donation creation"""
        donation = Donation.objects.create(
            name="John Doe",
            amount=Decimal("25.50")
        )
        self.assertIsNotNone(donation.pk)
        self.assertEqual(donation.name, "John Doe")
        self.assertEqual(donation.amount, Decimal("25.50"))
        self.assertIsNotNone(donation.created_at)

    def test_string_representation(self):
        """Test the __str__ method"""
        donation = Donation.objects.create(
            name="Jane Smith",
            amount=Decimal("100.00")
        )
        expected_str = "Jane Smith - $100.00"
        self.assertEqual(str(donation), expected_str)

    def test_minimum_amount_validation(self):
        """Test that donations below minimum amount are rejected"""
        donation = Donation(
            name="Test User",
            amount=Decimal("0.00")
        )
        with self.assertRaises(ValidationError):
            donation.full_clean()

    def test_valid_minimum_amount(self):
        """Test that minimum valid amount (0.01) is accepted"""
        donation = Donation.objects.create(
            name="Penny Donor",
            amount=Decimal("0.01")
        )
        self.assertIsNotNone(donation.pk)
        self.assertEqual(donation.amount, Decimal("0.01"))
