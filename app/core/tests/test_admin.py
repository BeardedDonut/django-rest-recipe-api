from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        # Create a test client that basically a dummy web-browser
        # in order to facilitate the testing process
        self.client = Client()

        # Create a test admin user
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin_user@1234.com',
            password='somepassword'
        )
        # Log in the test admin to client
        self.client.force_login(self.admin_user)

        # Create a test regular user
        self.user = get_user_model().objects.create_user(
            email='regular_user@some.com',
            password='regular_password',
            name='TestName'
        )

    def test_users_listed(self):
        """Test that users are listed on user page"""
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_user_change_page(self):
        """Test that user edit page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        """Test that user create page works"""
        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
