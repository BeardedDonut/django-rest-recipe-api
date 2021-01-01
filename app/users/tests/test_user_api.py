from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')


def create_user(**params):
    """A helper function to create users"""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the users public API"""

    def setup(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Creating a user with valid parameters successfully"""
        params = {
            'email': 'some_random_email@random.com',
            'password': '1234@1234',
            'name': 'MrRandom'
        }
        response = self.client.post(CREATE_USER_URL, params)

        # check for status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # check if the created user can be fetched from DB
        user = get_user_model().objects.get(**response.data)
        # check if created user password matches with the parameter sent
        self.assertTrue(user.check_password(params['password']))
        # check if the password is not included in the response object
        self.assertNotIn('password', response.data)

    def test_create_duplicate_user(self):
        """Test creating a user that already exists"""
        params = {
            'email': 'some_random_email@random.com',
            'password': '1234@1234',
            'name': 'MrRandom'
        }
        create_user(**params)

        response = self.client.post(CREATE_USER_URL, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_short_password(self):
        """Test that password is at least 8 characters long"""
        params = {
            'email': 'test@user.com',
            'password': 'short',
            'name': 'test'
        }
        response = self.client.post(CREATE_USER_URL, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=params['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for users"""
        params = {
            'email': 'test@random.com',
            'password': 'testpass',
        }
        create_user(**params)
        response = self.client.post(TOKEN_URL, params)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_for_invalid_credentials(self):
        """Test that token not created when invalid credentials are passed"""
        right_params = {
            'email': 'test@random.com',
            'password': 'right_password',
        }
        create_user(**right_params)

        wrong_params = {
            'email': 'test@random.com',
            'password': 'wrong_password',
        }
        response = self.client.post(TOKEN_URL, wrong_params)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test token not created when user is does not exist"""
        params = {
            'email': 'test@random.com',
            'password': 'some_random_password',
        }
        response = self.client.post(TOKEN_URL, params)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are included in the params"""
        params = {
            'email': 'test@random.com',
            'password': ''
        }
        response = self.client.post(TOKEN_URL, params)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
