import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.models import ScanResult, User
from app.services.scan_service import ScanService
from app.utils.database import get_db

router = APIRouter(tags=["Scan"])
scan_service = ScanService()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))


def _allowed_content_type(content_type: Optional[str]) -> bool:
    return content_type in {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _validate_image_magic(data: bytes, content_type: str) -> bool:
    if not data:
        return False
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/gif":
        return data.startswith(b"GIF87a") or data.startswith(b"GIF89a")
    if content_type == "image/webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


def _safe_extension(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(content_type, ".bin")


# ------------------- SCAN IMAGE ------------------- #
@router.post("/image")
async def scan_image(file: UploadFile = File(...)):
    if not _allowed_content_type(file.content_type):
        raise HTTPException(status_code=400, detail="Unsupported or missing image content type")

    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Uploaded file exceeds the maximum allowed size")
        chunks.append(chunk)

    content = b"".join(chunks)
    if not _validate_image_magic(content, file.content_type or ""):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    safe_name = f"{uuid.uuid4().hex}{_safe_extension(file.content_type or '')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to store uploaded image") from exc

    try:
        result = scan_service.scan_image(file_path)
    except (ValueError, TypeError) as exc:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a readable image",
        ) from exc
    except RuntimeError as exc:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="Scan processing failed") from exc

    return {
        "scan_result": result
    }


# ------------------- SCAN HISTORY (PAGINATED) ------------------- #
@router.get("/scans")
def get_scan_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit

    scoped_query = db.query(ScanResult).filter(ScanResult.user_id == current_user.id)

    total = scoped_query.count()

    results = (
        scoped_query
        .order_by(ScanResult.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "page": page,
        "limit": limit,
        "total_records": total,
        "data": [
            {
                "id": r.id,
                "image_path": r.image_path,
                "detected_expiry": r.detected_expiry,
                "confidence": r.confidence,
                "extracted_text": r.extracted_text,
                "created_at": r.created_at,
            }
            for r in results
        ],
    }