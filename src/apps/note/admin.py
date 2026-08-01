from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.note.models.notes import Note


@admin.register(Note)
class NoteAdmin(ModelAdmin):
    list_display = ("title", "owner", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("title", "content", "owner__phone")
    ordering = ("-created_at",)
