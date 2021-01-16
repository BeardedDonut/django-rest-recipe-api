from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """create and return a sample recipe"""
    defaults = {
        'title': 'sample_recipe',
        'time_minutes': 10,
        'price': 10.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTest(TestCase):
    """Test publicly available APIs of the Recipe"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required to access Recipe API"""
        response = self.client.get(RECIPE_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test Recipe APIs that authenticated users can access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='some_random_user@somewhere.com',
            password='some_random_pass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        # create a bunch of sample recipes
        sample_recipe(user=self.user)
        sample_recipe(user=self.user, title='Pizza')

        # make the API call
        response = self.client.get(RECIPE_URL)

        # retrieve manually from DB
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_auth_userd(self):
        """Test only authenticated user can access its own recipes"""
        # create a second user
        second_user = get_user_model().objects.create_user(
            email='second_sample_user@somewhere2.com',
            password='second_random_password'
        )

        # craete a bunch of sample recipes
        sample_recipe(user=second_user)
        sample_recipe(user=self.user)

        # make the API call
        response = self.client.get(RECIPE_URL)

        # retrieve manually from the DB
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)
