import uuid

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserFormDataDTO,
    UserRequestDTO,
    UserUpdateDTO,
    UserUpdateFormDataDTO,
)
from apps.user.exceptions import (
    FileUploadError,
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserError,
    UserNotFoundError,
)
from apps.user.models.users import User
from config.base.base_service import BaseService
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from ninja.files import UploadedFile


class UserService(BaseService):
    """Service layer for user-related business logic"""

    def __init__(self):
        super().__init__()

    def create_user(self, data: UserRequestDTO) -> User:
        """Create a new user with validation"""
        if User.objects.filter(phone=data.phone).exists():
            raise UserAlreadyExistsError(f"Phone number {data.phone} already exists")

        if data.email and User.objects.filter(email=data.email).exists():
            raise UserAlreadyExistsError(f"Email {data.email} already exists")

        try:
            user = User.objects.create(
                phone=data.phone,
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
                middle_name=data.middle_name,
                password=make_password(data.password),
                profile_image=data.profile_image,
                password_changed_at=timezone.now(),
            )
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to create user: {str(e)}") from e

    def create_user_with_file(
        self, data: UserFormDataDTO, profile_image: UploadedFile | None = None
    ) -> User:
        """Create a new user with form data and file upload to MinIO"""
        if User.objects.filter(phone=data.phone).exists():
            raise UserAlreadyExistsError(f"Phone number {data.phone} already exists")

        if data.email and User.objects.filter(email=data.email).exists():
            raise UserAlreadyExistsError(f"Email {data.email} already exists")

        try:
            # Upload image to MinIO if provided
            image_url = None
            if profile_image:
                image_url = self._upload_to_minio(profile_image)

            user = User.objects.create(
                phone=data.phone,
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
                middle_name=data.middle_name,
                password=make_password(data.password),
                profile_image=image_url,
                password_changed_at=timezone.now(),
            )
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to create user: {str(e)}") from e

    def _upload_to_minio(self, file: UploadedFile) -> str:
        """Upload file to MinIO and return the URL"""
        try:
            client = self.s3_client.get_client()

            # Ensure bucket exists (ideally this should be done once during app startup)
            try:
                client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            except Exception:
                client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

            # Generate unique filename
            file_extension = file.name.split(".")[-1] if "." in file.name else "jpg"
            filename = f"profile_images/{uuid.uuid4()}.{file_extension}"

            # Upload file
            client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                filename,
                ExtraArgs={"ContentType": file.content_type or "image/jpeg"},
            )

            # Return the URL using helper
            return self.s3_client.get_file_url(filename)

        except Exception as e:
            raise FileUploadError(f"File upload error: {str(e)}") from e

    def update_user(self, user: User, data: UserUpdateDTO) -> User:
        """Update user profile"""
        try:
            if data.email and data.email != user.email:
                if User.objects.filter(email=data.email).exclude(id=user.id).exists():
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
                user.set_password(data.password)

            user.save()
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to update user: {str(e)}") from e

    def update_user_with_file(
        self,
        user: User,
        data: UserUpdateFormDataDTO,
        profile_image: UploadedFile | None = None,
    ) -> User:
        """Update user profile with form data and file upload to MinIO"""
        try:
            if data.email and data.email != user.email:
                if User.objects.filter(email=data.email).exclude(id=user.id).exists():
                    raise UserAlreadyExistsError(f"Email {data.email} already exists")
                user.email = data.email

            if data.first_name:
                user.first_name = data.first_name
            if data.last_name:
                user.last_name = data.last_name
            if data.middle_name:
                user.middle_name = data.middle_name

            if profile_image:
                image_url = self._upload_to_minio(profile_image)
                user.profile_image = image_url

            user.save()
            return user
        except IntegrityError as e:
            raise UserError(f"Failed to update user: {str(e)}") from e

    def get_all_users(self, filters=None):
        """Get all users for admin list"""
        qs = User.objects.all()
        if filters:
            qs = filters.filter(qs)
        return qs

    def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Get user by ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with id {user_id} not found") from None

    def get_user_by_phone(self, phone: str) -> User:
        """Get user by phone"""
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with phone {phone} not found") from None

    def deactivate_user(self, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        user.save()
        return user

    def activate_user(self, user: User) -> User:
        """Activate user account"""
        user.is_active = True
        user.save()
        return user

    def change_password(self, user: User, data: ChangePasswordDTO) -> None:
        """Change user's password"""
        if data.new_password != data.confirm_password:
            raise InvalidPasswordError("New passwords do not match")

        try:
            user.set_password(data.new_password)
            user.password_changed_at = timezone.now()
            user.full_clean()  # Validate the new password
            user.save()
        except ValidationError as e:
            raise InvalidPasswordError(f"Password validation error: {str(e)}") from e
        except Exception as e:
            raise UserError(f"Failed to change password: {str(e)}") from e
