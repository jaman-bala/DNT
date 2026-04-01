from apps.common.services.s3_service import S3Service
from apps.user.services.auth_service import AuthService
from apps.user.services.blacklist_service import BlacklistService
from apps.user.services.user_service import UserService


class Container:
    """Enterprise-level DI Container for service management."""

    def __init__(self):
        self.s3_service = S3Service()
        self.blacklist_service = BlacklistService()
        self.user_service = UserService()
        self.auth_service = AuthService(blacklist_service=self.blacklist_service)


container = Container()
