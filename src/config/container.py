from apps.common.services.queue_service import QueueService
from apps.common.services.s3_service import S3Service
from apps.note.services.note_service import NoteService
from apps.user.services.auth_service import AuthService
from apps.user.services.blacklist_service import BlacklistService
from apps.user.services.user_service import UserService


class Container:
    """Enterprise-level DI Container for service management."""

    def __init__(self):
        self.s3_service = S3Service()
        self.queue_service = QueueService()
        self.blacklist_service = BlacklistService()
        self.note_service = NoteService()
        self.user_service = UserService(
            blacklist_service=self.blacklist_service,
            queue_service=self.queue_service,
        )
        self.auth_service = AuthService(
            blacklist_service=self.blacklist_service,
            queue_service=self.queue_service,
        )


container = Container()
