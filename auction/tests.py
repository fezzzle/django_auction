from django.test import TestCase
from auction.models import CustomUser


class TestUser(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(email='timmy@tommy.com')
        self.user.username = "Timmy"
        self.user.location = "Tartu"
        self.user.phone = 5300000

    def test_username(self):
        username = self.user.username
        self.assertEqual(username, "Timmy")

    def test_email(self):
        email = self.user.email
        self.assertEqual(email, 'timmy@tommy.com')

    def test_location(self):
        location = self.user.location
        self.assertEqual(location, "Tartu")
    
    def test_phone(self):
        phone = self.user.phone
        self.assertIsInstance(phone, int)
        self.assertEqual(phone, 5300000)


class TestAuction(TestCase):
    pass