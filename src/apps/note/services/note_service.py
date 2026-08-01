import uuid

from django.db.models import QuerySet

from apps.note.dto.schemas import NoteCreateDTO, NoteUpdateDTO
from apps.note.exceptions import NoteNotFoundError
from apps.note.models.notes import Note
from apps.user.models.users import User
from config.base.base_service import BaseService


class NoteService(BaseService):
    """
    Service layer for the Note domain — a reference implementation of the
    Controller -> Service -> Model pattern for non-auth resources. Every
    method is scoped to the requesting user's own notes.
    """

    async def list_notes(self, user: User) -> QuerySet[Note]:
        return Note.objects.filter(owner=user)

    async def get_note(self, user: User, note_id: uuid.UUID) -> Note:
        try:
            return await Note.objects.aget(id=note_id, owner=user)
        except Note.DoesNotExist:
            raise NoteNotFoundError() from None

    async def create_note(self, user: User, data: NoteCreateDTO) -> Note:
        return await Note.objects.acreate(
            owner=user, title=data.title, content=data.content
        )

    async def update_note(
        self, user: User, note_id: uuid.UUID, data: NoteUpdateDTO
    ) -> Note:
        note = await self.get_note(user, note_id)

        if data.title is not None:
            note.title = data.title
        if data.content is not None:
            note.content = data.content

        await note.asave()
        return note

    async def delete_note(self, user: User, note_id: uuid.UUID) -> None:
        note = await self.get_note(user, note_id)
        await note.adelete()
