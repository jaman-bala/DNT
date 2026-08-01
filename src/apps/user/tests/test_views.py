from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class UserAPITestCase(TestCase):
    """Test cases for User API endpoints"""

    def setUp(self):
        """Set up test data"""
        cache.clear()  # isolate rate-limit counters from other test cases
        self.user_data = {
            "phone": "+996500000000",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "Test",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.admin_user = User.objects.create_superuser(
            phone="+996500000001",
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
            middle_name="Admin",
        )

    def test_user_registration(self):
        """Test user registration endpoint"""
        new_user_data = {
            "phone": "+996500000002",
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "middle_name": "New",
        }

        response = self.client.post(
            "/api/v1/auth/register",
            data=new_user_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(phone="+996500000002").exists())

    def test_user_registration_duplicate_phone(self):
        """Test user registration with duplicate phone"""
        response = self.client.post(
            "/api/v1/auth/register",
            data=self.user_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)

    def test_user_login(self):
        """Test user login endpoint"""
        login_data = {"phone": "+996500000000", "password": "testpass123"}

        response = self.client.post(
            "/api/v1/auth/login", data=login_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        login_data = {"phone": "+996500000000", "password": "wrongpassword"}

        response = self.client.post(
            "/api/v1/auth/login", data=login_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)

    def test_get_current_user_authenticated(self):
        """Test get current user when authenticated"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        response = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["phone"], "+996500000000")

    def test_get_current_user_unauthenticated(self):
        """Test get current user when not authenticated"""
        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401)

    def test_update_current_user(self):
        """Test update current user profile"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "middle_name": "Updated",
            "email": "updated@example.com",
        }

        response = self.client.patch(
            "/api/v1/users/me_update",
            data=update_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.middle_name, "Updated")
        self.assertEqual(self.user.email, "updated@example.com")

    def test_list_users_admin(self):
        """Test list users endpoint for admin"""
        refresh = RefreshToken.for_user(self.admin_user)
        access_token = str(refresh.access_token)

        response = self.client.get(
            "/api/v1/users/", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 2)  # testuser + admin
        self.assertEqual(len(body["items"]), 2)

    def test_list_users_non_admin(self):
        """Test list users endpoint for non-admin user"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        response = self.client.get(
            "/api/v1/users/", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        self.assertEqual(response.status_code, 403)
