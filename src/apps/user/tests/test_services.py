import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.user.dto.schemas import UserRequestDTO, UserUpdateDTO
from apps.user.services.user_service import UserService

User = get_user_model()


class UserServiceTestCase(TestCase):
    """Test cases for UserService"""

    def setUp(self):
        """Set up test data"""
        self.user_data = UserRequestDTO(
            phone="+996500000000",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            middle_name="Test",
        )
        self.user = UserService.create_user(self.user_data)

    def test_create_user(self):
        """Test user creation"""
        new_user_data = UserRequestDTO(
            phone="+996500000001",
            email="newuser@example.com",
            password="newpass123",
            first_name="New",
            last_name="User",
            middle_name="New",
        )

        user = UserService.create_user(new_user_data)

        self.assertEqual(user.phone, "+996500000001")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.middle_name, "New")
        self.assertTrue(user.check_password("newpass123"))

    def test_create_user_duplicate_phone(self):
        """Test user creation with duplicate phone"""
        duplicate_data = UserRequestDTO(
            phone="+996500000000",  # Same as existing user
            email="different@example.com",
            password="pass123",
            first_name="Different",
            last_name="User",
            middle_name="Different",
        )

        with self.assertRaises(ValueError) as context:
            UserService.create_user(duplicate_data)

        self.assertIn("Phone number already exists", str(context.exception))

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        duplicate_data = UserRequestDTO(
            phone="+996500000001",
            email="test@example.com",  # Same as existing user
            password="pass123",
            first_name="Different",
            last_name="User",
            middle_name="Different",
        )

        with self.assertRaises(ValueError) as context:
            UserService.create_user(duplicate_data)

        self.assertIn("Email already exists", str(context.exception))

    def test_update_user(self):
        """Test user update"""
        update_data = UserUpdateDTO(
            first_name="Updated",
            last_name="User",
            middle_name="Updated",
            email="updated@example.com",
        )

        updated_user = UserService.update_user(self.user, update_data)

        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.last_name, "User")
        self.assertEqual(updated_user.middle_name, "Updated")
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_update_user_password(self):
        """Test user password update"""
        update_data = UserUpdateDTO(password="newpassword123")

        updated_user = UserService.update_user(self.user, update_data)

        self.assertTrue(updated_user.check_password("newpassword123"))

    def test_update_user_duplicate_email(self):
        """Test user update with duplicate email"""
        # Create another user
        UserService.create_user(
            UserRequestDTO(
                phone="+996500000001",
                email="another@example.com",
                password="pass123",
                first_name="Another",
                last_name="User",
                middle_name="Another",
            )
        )

        # Try to update first user with second user's email
        update_data = UserUpdateDTO(email="another@example.com")

        with self.assertRaises(ValueError) as context:
            UserService.update_user(self.user, update_data)

        self.assertIn("Email already exists", str(context.exception))

    def test_get_user_by_id(self):
        """Test get user by ID"""
        user = UserService.get_user_by_id(self.user.id)

        self.assertEqual(user, self.user)

    def test_get_user_by_id_not_found(self):
        """Test get user by non-existent ID"""
        user = UserService.get_user_by_id(uuid.uuid4())

        self.assertIsNone(user)

    def test_get_user_by_phone(self):
        """Test get user by phone"""
        user = UserService.get_user_by_phone("+996500000000")

        self.assertEqual(user, self.user)

    def test_get_user_by_phone_not_found(self):
        """Test get user by non-existent phone"""
        user = UserService.get_user_by_phone("+996500000001")

        self.assertIsNone(user)

    def test_deactivate_user(self):
        """Test user deactivation"""
        UserService.deactivate_user(self.user)
        self.user.refresh_from_db()

        self.assertFalse(self.user.is_active)

    def test_activate_user(self):
        """Test user activation"""
        # First deactivate
        UserService.deactivate_user(self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # Then activate
        UserService.activate_user(self.user)
        self.user.refresh_from_db()

        self.assertTrue(self.user.is_active)
