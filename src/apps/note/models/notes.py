from django.conf import settings
from django.db import models

from config.base.base_model import BaseModel


class Note(BaseModel):
    """
    Minimal owned resource — a reference implementation of the
    Controller -> Service -> Model pattern for domains that aren't auth.
    Copy this app's structure when adding your own models.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField("Title", max_length=255)
    content = models.TextField("Content", blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Заметка"
        verbose_name_plural = "Заметки"
        db_table = "notes"
        ordering = ["-created_at"]
