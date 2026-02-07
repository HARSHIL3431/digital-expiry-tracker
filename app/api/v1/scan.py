import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.services.scan_service import ScanService
from app.utils.database import SessionLocal
from app.models import ScanResult

router = APIRouter(prefix="/scan", tags=["Scan"])
scan_service = ScanService()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------- SCAN IMAGE ------------------- #
@router.post("/image")
async def scan_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = scan_service.scan_image(file_path)

    return{ 
        "scan_result": result
    }


# ------------------- SCAN HISTORY (PAGINATED) ------------------- #
@router.get("/scans")
def get_scan_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    db: Session = SessionLocal()
    try:
        offset = (page - 1) * limit

        total = db.query(ScanResult).count()

        results = (
            db.query(ScanResult)
            .order_by(ScanResult.scanned_at.desc())
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
                    "image_name": r.image_name,
                    "expiry_date": r.expiry_date,
                    "days_left": r.days_left,
                    "status": r.status,
                    "scanned_at": r.scanned_at,
                }
                for r in results
            ],
        }
    finally:
        db.close()
