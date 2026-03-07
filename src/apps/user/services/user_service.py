import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ninja.files import UploadedFile

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserFormDataDTO,
    UserRequestDTO,
    UserUpdateDTO,
    UserUpdateFormDataDTO,
)
from apps.user.models.users import User


class UserService:
    """Service layer for user-related business logic"""

    @staticmethod
    def create_user(data: UserRequestDTO) -> User:
        """Create a new user with validation"""
        if User.objects.filter(phone=data.phone).exists():
            raise ValueError("Phone number already exists")

        if User.objects.filter(email=data.email).exists():
            raise ValueError("Email already exists")

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
            raise ValueError(f"Failed to create user: {str(e)}") from e

    @staticmethod
    def create_user_with_file(
        data: UserFormDataDTO, profile_image: UploadedFile | None = None
    ) -> User:
        """Create a new user with form data and file upload to MinIO"""
        if User.objects.filter(phone=data.phone).exists():
            raise ValueError("Phone number already exists")

        if User.objects.filter(email=data.email).exists():
            raise ValueError("Email already exists")

        try:
            # Upload image to MinIO if provided
            image_url = None
            if profile_image:
                image_url = UserService._upload_to_minio(profile_image)

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
            raise ValueError(f"Failed to create user: {str(e)}") from e

    @staticmethod
    def _upload_to_minio(file: UploadedFile) -> str:
        """Upload file to MinIO and return the URL"""
        try:
            # Initialize MinIO client
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            # Create bucket if it doesn't exist
            try:
                s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    # Bucket doesn't exist, create it
                    s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                elif error_code == "403":
                    # Bucket exists but no access
                    pass
                else:
                    raise e

            # Generate unique filename
            file_extension = file.name.split(".")[-1] if "." in file.name else "jpg"
            filename = f"profile_images/{uuid.uuid4()}.{file_extension}"

            # Upload file
            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                filename,
                ExtraArgs={"ContentType": file.content_type or "image/jpeg"},
            )

            # Return the URL
            return f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"

        except ClientError as e:
            raise ValueError(f"Failed to upload file to MinIO: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"File upload error: {str(e)}") from e

    @staticmethod
    def update_user(user: User, data: UserUpdateDTO) -> User:
        """Update user profile"""
        try:
            if data.email and data.email != user.email:
                if User.objects.filter(email=data.email).exclude(id=user.id).exists():
                    raise ValueError("Email already exists")
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
            raise ValueError(f"Failed to update user: {str(e)}") from e

    @staticmethod
    def update_user_with_file(
        user: User,
        data: UserUpdateFormDataDTO,
        profile_image: UploadedFile | None = None,
    ) -> User:
        """Update user profile with form data and file upload to MinIO"""
        try:
            if data.email and data.email != user.email:
                if User.objects.filter(email=data.email).exclude(id=user.id).exists():
                    raise ValueError("Email already exists")
                user.email = data.email

            if data.first_name:
                user.first_name = data.first_name
            if data.last_name:
                user.last_name = data.last_name
            if data.middle_name:
                user.middle_name = data.middle_name

            if profile_image:
                image_url = UserService._upload_to_minio(profile_image)
                user.profile_image = image_url

            user.save()
            return user
        except IntegrityError as e:
            raise ValueError(f"Failed to update user: {str(e)}") from e

    @staticmethod
    def get_user_by_id(user_id: uuid.UUID) -> User | None:
        """Get user by ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_phone(phone: str) -> User | None:
        """Get user by phone"""
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None

    @staticmethod
    def deactivate_user(user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        user.save()
        return user

    @staticmethod
    def activate_user(user: User) -> User:
        """Activate user account"""
        user.is_active = True
        user.save()
        return user

    @staticmethod
    def change_password(user: User, data: ChangePasswordDTO) -> None:
        """Change user's password"""
        if data.new_password != data.confirm_password:
            raise ValueError("New passwords do not match")

        try:
            user.set_password(data.new_password)
            user.password_changed_at = timezone.now()
            user.full_clean()  # Validate the new password
            user.save()
        except ValidationError as e:
            raise ValueError(f"Password validation error: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Failed to change password: {str(e)}") from e
