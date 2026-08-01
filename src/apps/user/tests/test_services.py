import uuid

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.user.dto.schemas import ChangePasswordDTO, UserRequestDTO, UserUpdateDTO
from apps.user.exceptions import UserAlreadyExistsError, UserNotFoundError
from apps.user.services.user_service import UserService

User = get_user_model()


class UserServiceTestCase(TestCase):
    """Test cases for UserService"""

    def setUp(self):
        """Set up test data"""
        self.service = UserService()
        self.user_data = UserRequestDTO(
            phone="+996500000000",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            middle_name="Test",
        )
        self.user = async_to_sync(self.service.create_user)(self.user_data)

    async def test_create_user(self):
        """Test user creation"""
        new_user_data = UserRequestDTO(
            phone="+996500000001",
            email="newuser@example.com",
            password="newpass123",
            first_name="New",
            last_name="User",
            middle_name="New",
        )

        user = await self.service.create_user(new_user_data)

        self.assertEqual(user.phone, "+996500000001")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.middle_name, "New")
        self.assertTrue(user.check_password("newpass123"))

    async def test_create_user_duplicate_phone(self):
        """Test user creation with duplicate phone"""
        duplicate_data = UserRequestDTO(
            phone="+996500000000",  # Same as existing user
            email="different@example.com",
            password="pass1234",
            first_name="Different",
            last_name="User",
            middle_name="Different",
        )

        with self.assertRaises(UserAlreadyExistsError) as context:
            await self.service.create_user(duplicate_data)

        self.assertIn("already exists", str(context.exception))

    async def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        duplicate_data = UserRequestDTO(
            phone="+996500000001",
            email="test@example.com",  # Same as existing user
            password="pass1234",
            first_name="Different",
            last_name="User",
            middle_name="Different",
        )

        with self.assertRaises(UserAlreadyExistsError) as context:
            await self.service.create_user(duplicate_data)

        self.assertIn("already exists", str(context.exception))

    async def test_update_user(self):
        """Test user update"""
        update_data = UserUpdateDTO(
            first_name="Updated",
            last_name="User",
            middle_name="Updated",
            email="updated@example.com",
        )

        updated_user = await self.service.update_user(self.user, update_data)

        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.last_name, "User")
        self.assertEqual(updated_user.middle_name, "Updated")
        self.assertEqual(updated_user.email, "updated@example.com")

    async def test_update_user_password(self):
        """Test user password update"""
        update_data = UserUpdateDTO(password="newpassword123")

        updated_user = await self.service.update_user(self.user, update_data)

        self.assertTrue(updated_user.check_password("newpassword123"))

    async def test_update_user_duplicate_email(self):
        """Test user update with duplicate email"""
        # Create another user
        await self.service.create_user(
            UserRequestDTO(
                phone="+996500000001",
                email="another@example.com",
                password="pass1234",
                first_name="Another",
                last_name="User",
                middle_name="Another",
            )
        )

        # Try to update first user with second user's email
        update_data = UserUpdateDTO(email="another@example.com")

        with self.assertRaises(UserAlreadyExistsError) as context:
            await self.service.update_user(self.user, update_data)

        self.assertIn("already exists", str(context.exception))

    async def test_change_password_mismatch(self):
        """Changing the password with mismatched confirmation should fail"""
        from apps.user.exceptions import InvalidPasswordError

        data = ChangePasswordDTO(
            new_password="newpassword123", confirm_password="different123"
        )

        with self.assertRaises(InvalidPasswordError):
            await self.service.change_password(self.user, data)

    async def test_get_user_by_id(self):
        """Test get user by ID"""
        user = await self.service.get_user_by_id(self.user.id)

        self.assertEqual(user, self.user)

    async def test_get_user_by_id_not_found(self):
        """Test get user by non-existent ID"""
        with self.assertRaises(UserNotFoundError):
            await self.service.get_user_by_id(uuid.uuid4())

    async def test_get_user_by_phone(self):
        """Test get user by phone"""
        user = await self.service.get_user_by_phone("+996500000000")

        self.assertEqual(user, self.user)

    async def test_get_user_by_phone_not_found(self):
        """Test get user by non-existent phone"""
        with self.assertRaises(UserNotFoundError):
            await self.service.get_user_by_phone("+996500000001")

    async def test_deactivate_user(self):
        """Test user deactivation"""
        await self.service.deactivate_user(self.user)
        await self.user.arefresh_from_db()

        self.assertFalse(self.user.is_active)

    async def test_activate_user(self):
        """Test user activation"""
        # First deactivate
        await self.service.deactivate_user(self.user)
        await self.user.arefresh_from_db()
        self.assertFalse(self.user.is_active)

        # Then activate
        await self.service.activate_user(self.user)
        await self.user.arefresh_from_db()

        self.assertTrue(self.user.is_active)
