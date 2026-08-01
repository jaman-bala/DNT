from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.note.models.notes import Note

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class NoteAPITestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000050", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            phone="+996500000051", password="testpass123"
        )
        self.auth_header = f"Bearer {RefreshToken.for_user(self.user).access_token}"
        self.other_auth_header = (
            f"Bearer {RefreshToken.for_user(self.other_user).access_token}"
        )

    def test_list_requires_auth(self):
        response = self.client.get("/api/v1/notes/")
        self.assertEqual(response.status_code, 401)

    def test_create_and_get_note(self):
        create = self.client.post(
            "/api/v1/notes/",
            data={"title": "Shopping list", "content": "Milk, eggs"},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(create.status_code, 200)
        note_id = create.json()["id"]

        response = self.client.get(
            f"/api/v1/notes/{note_id}", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Shopping list")
        self.assertEqual(response.json()["content"], "Milk, eggs")

    def test_list_only_returns_own_notes(self):
        Note.objects.create(owner=self.user, title="Mine", content="")
        Note.objects.create(owner=self.other_user, title="Theirs", content="")

        response = self.client.get(
            "/api/v1/notes/", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["items"][0]["title"], "Mine")

    def test_get_another_users_note_is_404(self):
        note = Note.objects.create(owner=self.other_user, title="Theirs", content="")

        response = self.client.get(
            f"/api/v1/notes/{note.id}", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_note_is_404(self):
        import uuid

        response = self.client.get(
            f"/api/v1/notes/{uuid.uuid4()}", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 404)

    def test_update_note(self):
        note = Note.objects.create(owner=self.user, title="Old", content="old")

        response = self.client.patch(
            f"/api/v1/notes/{note.id}",
            data={"title": "New"},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.title, "New")
        self.assertEqual(note.content, "old")

    def test_update_another_users_note_is_404(self):
        note = Note.objects.create(owner=self.other_user, title="Theirs", content="")

        response = self.client.patch(
            f"/api/v1/notes/{note.id}",
            data={"title": "Hijacked"},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(response.status_code, 404)
        note.refresh_from_db()
        self.assertEqual(note.title, "Theirs")

    def test_delete_note(self):
        note = Note.objects.create(owner=self.user, title="Bye", content="")

        response = self.client.delete(
            f"/api/v1/notes/{note.id}", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Note.objects.filter(id=note.id).exists())

    def test_delete_another_users_note_is_404(self):
        note = Note.objects.create(owner=self.other_user, title="Theirs", content="")

        response = self.client.delete(
            f"/api/v1/notes/{note.id}", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Note.objects.filter(id=note.id).exists())
