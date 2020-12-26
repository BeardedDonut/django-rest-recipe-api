from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):

    def test_create_user_with_email_successfully(self):
        """Test creating a user with an email is successful"""
        email = 'test_email@1234.com'
        password = 'test1234@@'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """Test the email for a new user is normalized"""
        email = "test_user@GMAIL.COM"
        user = get_user_model().objects.create_user(
            email=email,
            password='some_password'
        )

        self.assertEqual(user.email, email.lower())
