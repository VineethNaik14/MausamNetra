"""
Media upload service.

Handles safe local storage of citizen-submitted photos/videos. Designed so
that swapping to S3/MinIO later only requires changing this module (the
Report model just stores a URL/path string, and callers only see
`save_upload()` / the returned public path).
"""
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileUploadError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MediaService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.images_dir = self.upload_dir / "images"
        self.videos_dir = self.upload_dir / "videos"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, filename: str) -> tuple[str, bool]:
        """Returns (extension, is_image). Raises FileUploadError if not allowed."""
        ext = Path(filename).suffix.lower().lstrip(".")
        if not ext:
            raise FileUploadError("File must have an extension")

        if ext in settings.allowed_image_extensions_set:
            return ext, True
        if ext in settings.allowed_video_extensions_set:
            return ext, False

        raise FileUploadError(
            f"File type '.{ext}' is not allowed. Allowed: "
            f"{sorted(settings.allowed_image_extensions_set | settings.allowed_video_extensions_set)}"
        )

    async def save_upload(self, file: UploadFile) -> str:
        """
        Validate and persist an uploaded file. Returns a relative URL path
        (e.g. 'uploads/images/<uuid>.jpg') to store on the Report record.
        """
        if not file.filename:
            raise FileUploadError("Uploaded file has no filename")

        ext, is_image = self._validate_extension(file.filename)

        # Enforce size limit by reading in chunks (avoid loading huge files into memory blindly).
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise FileUploadError(
                f"File too large: {len(contents)} bytes (max {settings.MAX_UPLOAD_SIZE} bytes)"
            )
        if len(contents) == 0:
            raise FileUploadError("Uploaded file is empty")

        # Generate a safe, unguessable filename - never trust the client-supplied name.
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        target_dir = self.images_dir if is_image else self.videos_dir
        target_path = target_dir / safe_name

        # Defense in depth against path traversal, even though safe_name is generated.
        resolved = target_path.resolve()
        if not str(resolved).startswith(str(self.upload_dir.resolve())):
            raise FileUploadError("Invalid upload path")

        with open(target_path, "wb") as f:
            f.write(contents)

        relative = os.path.join(settings.UPLOAD_DIR, "images" if is_image else "videos", safe_name)
        logger.info("Saved upload to %s", relative)
        return relative


def get_media_service() -> MediaService:
    return MediaService()
