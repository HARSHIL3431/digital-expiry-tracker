from fastapi import APIRouter

router = APIRouter(prefix="/scan", tags=["OCR"])


@router.get("/health")
def scan_health():
    return {"status": "scan api working"}
