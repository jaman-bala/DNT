import uuid

from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserRequestDTO,
    UserUpdateDTO,
)
from apps.user.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserError,
    UserNotFoundError,
)
from apps.user.models.users import User
from config.base.base_service import BaseService


class UserService(BaseService):
    """Service layer for user-related business logic"""

    def __init__(self):
        super().__init__()

    async def create_user(
        self,
        data: UserRequestDTO,
    ) -> User:
        """Create a new user with validation"""
        if await User.objects.filter(phone=data.phone).aexists():
            raise UserAlreadyExistsError(f"Phone number {data.phone} already exists")

        if data.email and await User.objects.filter(email=data.email).aexists():
            raise UserAlreadyExistsError(f"Email {data.email} already exists")

        try:
            image_url = data.profile_image

            # make_password is CPU bound, sync_to_async is fine
            hashed_password = await sync_to_async(make_password)(data.password)

            user = await User.objects.acreate(
                phone=data.phone,
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
                middle_name=data.middle_name,
                password=hashed_password,
                profile_image=image_url,
                password_changed_at=timezone.now(),
            )
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to create user: {str(e)}") from e

    async def update_user(self, user: User, data: UserUpdateDTO) -> User:
        """Update user profile"""
        try:
            if data.email and data.email != user.email:
                if (
                    await User.objects
                    .filter(email=data.email)
                    .exclude(id=user.id)
                    .aexists()
                ):
                    raise UserAlreadyExistsError(f"Email {data.email} already exists")
                user.email = data.email

            if data.first_name:
                user.first_name = data.first_name
            if data.last_name:
                user.last_name = data.last_name
            if data.middle_name:
                user.middle_name = data.middle_name

            if data.profile_image:
                user.profile_image = data.profile_image

            if data.password:
                await sync_to_async(user.set_password)(data.password)
                user.password_changed_at = timezone.now()

            await user.asave()
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to update user: {str(e)}") from e

    async def get_all_users(self, filters=None):
        """Get all users for admin list"""
        qs = User.objects.all()
        if filters:
            qs = filters.filter(qs)
        return qs

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Get user by ID"""
        try:
            return await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with id {user_id} not found") from None

    async def get_user_by_phone(self, phone: str) -> User:
        """Get user by phone"""
        try:
            return await User.objects.aget(phone=phone)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with phone {phone} not found") from None

    async def deactivate_user(self, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        await user.asave()
        return user

    async def activate_user(self, user: User) -> User:
        """Activate user account"""
        user.is_active = True
        await user.asave()
        return user

    async def change_password(self, user: User, data: ChangePasswordDTO) -> None:
        """Change user's password"""
        if data.new_password != data.confirm_password:
            raise InvalidPasswordError("New passwords do not match")

        try:
            # set_password is CPU bound, wrap it
            await sync_to_async(user.set_password)(data.new_password)
            user.password_changed_at = timezone.now()
            # full_clean might have DB calls if there are unique constraints, wrap it
            await sync_to_async(user.full_clean)()
            await user.asave()
        except ValidationError as e:
            raise InvalidPasswordError(f"Password validation error: {str(e)}") from e
        except Exception as e:
            raise UserError(f"Failed to change password: {str(e)}") from e
