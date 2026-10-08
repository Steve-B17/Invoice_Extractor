import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

CHUNK_SIZE = 1024 * 1024  # 1 MB

CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


def detect_file_type(header: bytes) -> str | None:
    """Identify the file by its first bytes (magic numbers), not by its name
    or the Content-Type header, which the client can fake."""
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"%PDF-"):
        return "pdf"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


def save_upload(file: UploadFile, user_id: int) -> tuple[str, str]:
    """Validate and save an uploaded file. Returns (stored_path, content_type)."""
    max_bytes = settings.max_upload_mb * 1024 * 1024

    header = file.file.read(16)
    if not header:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    ext = detect_file_type(header)
    if ext is None:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a JPG, PNG, WebP or PDF.",
        )
    file.file.seek(0)

    user_dir = Path(settings.upload_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    # Random server-chosen name: never use the client's filename for the path
    destination = user_dir / f"{uuid.uuid4().hex}.{ext}"

    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum is {settings.max_upload_mb} MB.",
                    )
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return str(destination), CONTENT_TYPES[ext]