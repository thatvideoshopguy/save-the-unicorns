from django.test import TestCase

from apps.accounts.tests.factories import UserFactory


class UserModelTestCase(TestCase):
    def test_create(self):
        user = UserFactory.create()
        self.assertIsNotNone(user.pk)
