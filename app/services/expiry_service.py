from datetime import date
from typing import List, Dict, Any, Optional


# ---------------- LEGACY (KEEP THIS) ---------------- #

def get_expiry_status(expiry_date: date) -> dict:
    """
    Determine expiry status based on today's date.

    Rules:
    - expired      -> expiry_date < today
    - near_expiry  -> expiry_date within next 30 days
    - safe         -> expiry_date > 30 days
    """

    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "expired"
    elif days_left <= 30:
        status = "near_expiry"
    else:
        status = "safe"

    return {
        "expiry_date": expiry_date,
        "days_left": days_left,
        "status": status,
    }


# ---------------- PHASE 2 SERVICE ---------------- #

class ExpiryService:
    """
    High-level expiry decision service.
    Works with OCR + parser output.
    """

    # ---------- SINGLE DATE ---------- #

    def evaluate_expiry(self, expiry_date: date) -> Dict[str, Any]:
        """
        Wrapper around legacy logic.
        """
        result = get_expiry_status(expiry_date)
        result["is_valid"] = expiry_date >= date(2000, 1, 1)
        return result

    # ---------- MULTIPLE CANDIDATES ---------- #

    def evaluate_candidates(
        self,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Takes expiry candidates from OCR parsing layer
        and evaluates them for suggestion & UI.
        """

        if not candidates:
            return {
                "candidates": [],
                "suggested": None,
                "needs_confirmation": True,
            }

        enriched = []

        for c in candidates:
            expiry_date = date.fromisoformat(c["normalized"])
            status_info = get_expiry_status(expiry_date)

            enriched.append({
                **c,
                **status_info,
            })

        # Prefer:
        # 1. not expired 
        # 2. highest confidence
        # 3. farthest expiry date
        enriched.sort(
            key=lambda x: (
                x["status"] == "expired",  # expired goes last
                -x["confidence"],         # higher confidence first
                -x["days_left"]         # farther expiry first
            )
        )

        suggested = enriched[0]

        return {
            "candidates": enriched,
            "suggested": suggested,
            "needs_confirmation": True,  # ALWAYS true by design
        }
