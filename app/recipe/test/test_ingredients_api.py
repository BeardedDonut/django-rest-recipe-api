from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test the public APIs of the Ingredient"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for Ingredient APIs"""
        response = self.client.get(INGREDIENT_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test Ingredients private APIs"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='sample_user@somewhere.com',
            password='some_random_password'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retreiving the list of ingredients"""
        # first create a bunch of sample ingredients
        Ingredient.objects.create(user=self.user, name='Black Pepper')
        Ingredient.objects.create(user=self.user, name='Salt')

        # retrieve the results direcly from the database and serilize them
        response = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_visilble_only_to_user(self):
        """
        Test that only ingredients that are related to the authenticated user
        are returned
        """
        # create a 'second sample user'
        second_user = get_user_model().objects.create_user(
            email='second_sample_user@somewhere2.com',
            password='second_user_pass'
        )
        # create an ingredient using the 'second_sample_user'
        Ingredient.objects.create(user=second_user, name='Egg')

        # create an ingredient with the default sample user
        ingred_2 = Ingredient.objects.create(user=self.user, name='Olive Oil')

        # make the API call
        response = self.client.get(INGREDIENT_URL)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingred_2.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient successfully"""
        # prepare the paramaters a new ingredient
        params = {'name': 'Potato'}

        # make the API call
        self.client.post(INGREDIENT_URL, params)

        # run the assertions
        is_existing = Ingredient.objects.filter(
            user=self.user,
            name=params['name']
        ).exists()
        self.assertTrue(is_existing)

    def test_create_ingredient_invalid(self):
        """Test creating an invalid ingredient"""
        # parepare the parameters for the invalid ingredient
        params = {'name': ''}

        # make the API call
        response = self.client.post(INGREDIENT_URL, params)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
