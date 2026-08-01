class NoteError(Exception):
    """Base class for all note-related errors."""

    def __init__(self, message: str, code: str = "note_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class NoteNotFoundError(NoteError):
    """
    Raised both when a note doesn't exist and when it exists but belongs to
    someone else — the API deliberately can't tell the two apart, so it
    can't be used to enumerate other users' note IDs.
    """

    def __init__(self, message: str = "Note not found"):
        super().__init__(message, code="note_not_found")
