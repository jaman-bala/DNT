import uuid

from ninja import Router
from ninja.pagination import paginate

from apps.note.dto.schemas import NoteCreateDTO, NoteResponseDTO, NoteUpdateDTO
from config.auth.authentication import UnifiedJWTAuthentication
from config.container import container
from config.pagination import CustomPagination

router = Router(tags=["Notes"])


@router.get("/", response=list[NoteResponseDTO], auth=UnifiedJWTAuthentication())
@paginate(CustomPagination)
async def list_notes(request):
    return await container.note_service.list_notes(request.user)


@router.post("/", response=NoteResponseDTO, auth=UnifiedJWTAuthentication())
async def create_note(request, data: NoteCreateDTO):
    return await container.note_service.create_note(request.user, data)


@router.get("/{note_id}", response=NoteResponseDTO, auth=UnifiedJWTAuthentication())
async def get_note(request, note_id: uuid.UUID):
    return await container.note_service.get_note(request.user, note_id)


@router.patch("/{note_id}", response=NoteResponseDTO, auth=UnifiedJWTAuthentication())
async def update_note(request, note_id: uuid.UUID, data: NoteUpdateDTO):
    return await container.note_service.update_note(request.user, note_id, data)


@router.delete("/{note_id}", auth=UnifiedJWTAuthentication())
async def delete_note(request, note_id: uuid.UUID):
    await container.note_service.delete_note(request.user, note_id)
    return {"message": "Note deleted"}
