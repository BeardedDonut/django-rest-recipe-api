import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return a Recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample Tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Black Pepper'):
    """Create and return a sample Ingredient"""
    return Ingredient.objects.create(user=user, name=name)


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

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        # create a sample recipe
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        # get the sample recipe's url & get recipe detail by making API call
        url = detail_url(recipe.id)
        response = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        # run the assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic (Without Tags) Recipe object"""
        params = {
            'title': 'Red Velvet Cake',
            'time_minutes': 30,
            'price': 10.00
        }
        response = self.client.post(RECIPE_URL, params)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in params.keys():
            self.assertEqual(params[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Desert')
        params = {
            'title': 'Avocade Lime Cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 100,
            'price': 35.00
        }
        response = self.client.post(RECIPE_URL, params)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ing1 = sample_ingredient(user=self.user, name='Red Pepper')
        ing2 = sample_ingredient(user=self.user, name='Salt')
        params = {
            'title': 'Steak',
            'ingredients': [ing1.id, ing2.id],
            'time_minutes': 50,
            'price': 15.00
        }
        response = self.client.post(RECIPE_URL, params)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ing1, ingredients)
        self.assertIn(ing2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with PATCH"""
        # create a sample recipe
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name='Desert'))

        # create fields that should be updated
        new_tag = sample_tag(user=self.user, name='Main Course')
        params = {
            'title': 'Pizza',
            'tags': [new_tag.id]
        }

        # get recipe specific url
        url = detail_url(recipe.id)

        # make the API call
        self.client.patch(url, params)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, params['title'])
        self.assertIn(new_tag, recipe.tags.all())
        self.assertEqual(len(recipe.tags.all()), 1)

    def test_full_update_recipe(self):
        """Test updating a recipe with PUT"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name='Desert'))

        new_tag1 = sample_tag(user=self.user, name='Main Course')
        new_tag2 = sample_tag(user=self.user, name='Pizza')
        new_ing1 = sample_ingredient(user=self.user, name='Salt')
        new_ing2 = sample_ingredient(user=self.user, name='Pepperoni')
        params = {
            'title': 'Pepperoni Pizza',
            'time_minutes': 33,
            'tags': [new_tag1.id, new_tag2.id],
            'ingredients': [new_ing1.id, new_ing2.id],
            'price': 15.00
        }

        url = detail_url(recipe.id)
        self.client.put(url, params)
        recipe.refresh_from_db()
        self.assertEqual(recipe.time_minutes, params['time_minutes'])
        self.assertEqual(recipe.price, params['price'])
        self.assertEqual(recipe.title, params['title'])

        self.assertEqual(len(recipe.tags.all()), 2)
        self.assertEqual(len(recipe.ingredients.all()), 2)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user, title='Pepperoni Pizza')
        recipe2 = sample_recipe(user=self.user, title='Cheese Burger')
        tag1 = sample_tag(user=self.user, name='Pizza')
        tag2 = sample_tag(user=self.user, name='Burger')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Ice Cream')

        response = self.client.get(
            RECIPE_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe1 = sample_recipe(user=self.user, title='Cheese Burger')
        recipe2 = sample_recipe(user=self.user, title='Mushroom Burger')
        ingredient1 = sample_ingredient(user=self.user, name='Cheese')
        ingredient2 = sample_ingredient(user=self.user, name='Mushroom')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Steak')

        response = self.client.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)


class RecipeImageUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test_user@somewhere.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_success(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (20, 20))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            response = self.client.post(
                url,
                {'image': ntf},
                format='multipart'
            )

        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        response = self.client.post(
            url,
            {'image': 'notimage'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
