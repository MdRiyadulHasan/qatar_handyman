from pathlib import Path
from uuid import uuid4
from django.core.files.storage import FileSystemStorage


class EditorImageStorage(FileSystemStorage):
    """Keep editor uploads within the project's media/editor directory."""
    def get_available_name(self, filename, max_length=None):
        extension = Path(filename).suffix.lower()
        return super().get_available_name(f"editor/{uuid4().hex}{extension}", max_length=max_length)
