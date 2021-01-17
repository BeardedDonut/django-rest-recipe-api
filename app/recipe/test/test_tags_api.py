from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerilizer

TAG_URL = reverse('recipe:tag-list')


class PublicTagsApiTest(TestCase):
    """Test the Tag public APIs"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        response = self.client.get(TAG_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test the authorized user Tag API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@somewhere.com',
            password='random_strong_password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving Tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Drink')
        Tag.objects.create(user=self.user, name='Main-Course')

        response = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerilizer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='second_user@somewhere.com',
            password='second_random_password'
        )

        Tag.objects.create(user=user2, name='Fruit')
        tag = Tag.objects.create(user=self.user, name='Ice-Cream')

        response = self.client.get(TAG_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)

    def test_create_tags_successful(self):
        """Test creating a new tag"""
        params = {'name': 'Test-Tag'}
        self.client.post(TAG_URL, params)

        is_existing = Tag.objects.filter(
            user=self.user,
            name=params['name']
        ).exists()

        self.assertTrue(is_existing)

    def test_create_tag_invalid_name(self):
        """Test creating a new tag with invalid name"""
        params = {'name': ''}
        response = self.client.post(TAG_URL, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtereing tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Scrambled Eggs',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe.tags.add(tag1)

        response = self.client.get(TAG_URL, {'assigned_only': 1})
        serializer1 = TagSerilizer(tag1)
        serializer2 = TagSerilizer(tag2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtereing tags by assigned returnes unique items"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Scrambled Egg',
            price=5.00,
            time_minutes=10
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Omelet',
            price=5.00,
            time_minutes=12
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        response = self.client.get(TAG_URL, {'assigned_only': 1})
        self.assertEqual(len(response.data), 1)
