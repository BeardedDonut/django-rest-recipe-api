from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='test@somewhere.com', password='testpassword'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


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

    def test_new_user_invalid_email(self):
        """Test creating a user without valid email address"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "test1234")

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            email='test@superusers.com',
            password='superstrongpassword'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tags' string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredients_str(self):
        """Test the ingredient string representation"""
        sample_ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='lemon'
        )
        self.assertEqual(str(sample_ingredient), sample_ingredient.name)

    def test_recipe_str(self):
        """Test the Recipe string representation"""
        sample_recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Cheese Burger',
            time_minutes=50,
            price=11.50
        )

        self.assertEqual(str(sample_recipe), sample_recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
