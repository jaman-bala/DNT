from datetime import datetime
from uuid import UUID

from ninja import Field, Schema
from pydantic import ConfigDict

from config.types import (
    FirstName,
    LastName,
    MiddleName,
    PasswordStr,
    PhoneStr,
)


class UserRequestDTO(Schema):
    phone: PhoneStr = Field(
        ...,
        description="Phone number",
        example="+996500500500",
    )
    email: str | None = Field(
        None, description="Email address", example="admin@example.com"
    )
    password: PasswordStr = Field(..., description="Password", example="P@sSw0rd-312!")
    first_name: FirstName | None = Field(
        None, description="First name", example="Mirbek"
    )
    last_name: LastName | None = Field(
        None, description="Last name", example="Atabekov"
    )
    middle_name: MiddleName | None = Field(
        None, description="Middle name", example="Smith"
    )
    profile_image: str | None = Field(None, description="Profile image URL")


class UserFormDataDTO(Schema):
    phone: PhoneStr = Field(
        ...,
        description="Phone number",
        example="+996500500500",
    )
    email: str | None = Field(
        None, description="Email address", example="admin@example.com"
    )
    password: PasswordStr = Field(..., description="Password", example="password")
    first_name: FirstName | None = Field(None, description="First name")
    last_name: LastName | None = Field(None, description="Last name")
    middle_name: MiddleName | None = Field(None, description="Middle name")


class UserResponseDTO(Schema):
    id: UUID = Field(..., description="User ID")
    phone: PhoneStr = Field(..., description="Phone number")
    email: str | None = Field(None, description="Email address")
    first_name: FirstName | None = Field(None, description="First name")
    last_name: LastName | None = Field(None, description="Last name")
    middle_name: MiddleName | None = Field(None, description="Middle name")
    profile_image: str | None = Field(None, description="Profile image URL")
    is_active: bool = Field(..., description="User active status")
    date_joined: datetime = Field(..., description="Registration date")
    password_change_required: bool = Field(
        False, description="Is password change required"
    )

    model_config = ConfigDict(from_attributes=True)


class UserUpdateDTO(Schema):
    email: str | None = Field(None, description="Email address")
    first_name: FirstName | None = Field(None, description="First name")
    last_name: LastName | None = Field(None, description="Last name")
    middle_name: MiddleName | None = Field(None, description="Middle name")
    profile_image: str | None = Field(None, description="Profile image URL")
    password: PasswordStr | None = Field(None, description="New password")


class UserUpdateFormDataDTO(Schema):
    email: str | None = Field(None, description="Email address")
    first_name: FirstName | None = Field(None, description="First name")
    last_name: LastName | None = Field(None, description="Last name")
    middle_name: MiddleName | None = Field(None, description="Middle name")


class LoginRequestDTO(Schema):
    phone: str = Field(..., description="Phone number", example="+996500500500")
    password: str = Field(..., description="Password", example="P@sSw0rd-312!")


class LoginResponseDTO(Schema):
    access: str = Field(..., description="Access token")
    refresh: str = Field(..., description="Refresh token")
    last_login: datetime | None = Field(None, description="Last login date")
    password_change_required: bool = Field(
        False, description="Is password change required"
    )

    model_config = ConfigDict(from_attributes=True)


class RefreshRequestDTO(Schema):
    refresh: str = Field(..., description="Refresh token")


class RefreshResponseDTO(Schema):
    access: str = Field(..., description="New access token")


class ErrorResponseDTO(Schema):
    detail: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")


class ChangePasswordDTO(Schema):
    new_password: PasswordStr = Field(..., description="New password")
    confirm_password: PasswordStr = Field(..., description="Confirm new password")
