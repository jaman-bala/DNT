from ninja import NinjaAPI

from apps.common.controllers.v1.upload import router as common_router_v1
from apps.note.controllers.v1.notes import router as note_router_v1
from apps.note.exceptions import NoteError, NoteNotFoundError
from apps.user.controllers.v1.urls import router as user_router_v1
from apps.user.exceptions import (
    FileUploadError,
    InvalidPasswordError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserError,
    UserNotFoundError,
)
from config.openapi import Scalar

api_v1 = NinjaAPI(
    title="API v1",
    version="1.1",
    description="Framework Django-Ninja-Template DNT (Version 1)",
    docs=Scalar(),
)


@api_v1.get("/health/", tags=["Healthcheck"])
def healthcheck(request):
    return {"status": "ok"}


@api_v1.exception_handler(UserNotFoundError)
def handle_not_found(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=404)


@api_v1.exception_handler(UserAlreadyExistsError)
def handle_conflict(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=409)


@api_v1.exception_handler(InvalidPasswordError)
def handle_invalid_password(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=400)


@api_v1.exception_handler(UserError)
def handle_user_error(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=400)


@api_v1.exception_handler(FileUploadError)
def handle_file_upload_error(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=400)


@api_v1.exception_handler(InvalidTokenError)
def handle_invalid_token_error(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=400)


@api_v1.exception_handler(NoteNotFoundError)
def handle_note_not_found(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=404)


@api_v1.exception_handler(NoteError)
def handle_note_error(request, exc):
    return api_v1.create_response(request, {"detail": str(exc)}, status=400)


# Add routers
api_v1.add_router("/common", common_router_v1)
api_v1.add_router("/notes", note_router_v1)
api_v1.add_router("", user_router_v1)
