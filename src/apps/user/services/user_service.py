import logging
import uuid

from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.common.services.queue_service import QueueService
from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserRequestDTO,
    UserUpdateDTO,
)
from apps.user.exceptions import (
    InvalidPasswordError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserError,
    UserNotFoundError,
)
from apps.user.models.users import User
from apps.user.services.blacklist_service import BlacklistService
from apps.user.utils.tokens import (
    EMAIL_VERIFICATION_TOKEN_LIFETIME,
    generate_action_token,
    verify_action_token,
)
from config.base.base_service import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Service layer for user-related business logic"""

    def __init__(
        self, blacklist_service: BlacklistService, queue_service: QueueService
    ):
        super().__init__()
        self.blacklist_service = blacklist_service
        self.queue_service = queue_service

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
                # Changing the email means it needs to be re-verified — otherwise a
                # stolen short-lived access token could be used to silently repoint
                # password-reset emails to an attacker's inbox.
                user.email_verified = False

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

    async def request_email_verification(self, user: User) -> None:
        """Enqueue a verification email for the given (authenticated) user."""
        if not user.email:
            raise UserError("No email address on file", code="no_email")

        token = generate_action_token(
            user, "email_verification", EMAIL_VERIFICATION_TOKEN_LIFETIME
        )
        try:
            await self.queue_service.enqueue(
                "send_verification_email", str(user.id), token
            )
        except Exception:
            logger.warning("Failed to enqueue verification email for %s", user.email)

    async def confirm_email_verification(self, token: str) -> None:
        """Verify an email-verification token and mark the email as verified."""
        user_id, jti, exp = await verify_action_token(
            token, "email_verification", self.blacklist_service
        )
        try:
            user = await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            raise InvalidTokenError() from None

        user.email_verified = True
        await user.asave()

        # Single-use: blacklist immediately so the same link can't be replayed.
        await self.blacklist_service.add_to_blacklist(jti, exp)
