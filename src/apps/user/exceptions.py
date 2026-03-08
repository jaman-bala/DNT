from typing import Any


class UserError(Exception):
    """Base class for all user-related errors."""

    def __init__(self, message: str, code: str = "user_error", details: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details


class UserAlreadyExistsError(UserError):
    """Raised when a user with the same phone or email already exists."""

    def __init__(self, message: str = "User already exists", details: Any = None):
        super().__init__(message, code="user_already_exists", details=details)


class UserNotFoundError(UserError):
    """Raised when a user is not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, code="user_not_found")


class InvalidPasswordError(UserError):
    """Raised when password validation fails."""

    def __init__(self, message: str = "Invalid password"):
        super().__init__(message, code="invalid_password")


class FileUploadError(UserError):
    """Raised when a file upload fails."""

    def __init__(self, message: str = "Failed to upload file"):
        super().__init__(message, code="file_upload_error")
