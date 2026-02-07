from datetime import datetime
from typing import List, Dict


class InventoryService:
    """
    Inventory memory & auto-suggestion service.
    Human-in-the-loop by design.
    """

    def __init__(self):
        # In-memory store (Phase 3)
        # key = product name (lowercase)
        self._inventory: Dict[str, Dict] = {}

    # ---------------- CONFIRMATION ---------------- #

    def confirm_product(self, product_name: str) -> None:
        """
        Called when user confirms a product name.
        """
        key = product_name.strip().lower()
        now = datetime.utcnow()

        if key in self._inventory:
            self._inventory[key]["count"] += 1
            self._inventory[key]["last_used"] = now
        else:
            self._inventory[key] = {
                "name": product_name.strip(),
                "count": 1,
                "last_used": now,
            }

    # ---------------- SUGGESTIONS ---------------- #

    def suggest_products(self, prefix: str, limit: int = 5) -> Dict:
        """
        Suggest product names based on prefix, frequency, and recency.
        """
        prefix = prefix.strip().lower()

        if not prefix:
            return {
                "suggestions": [],
                "needs_confirmation": True
            }

        matches = []

        for key, record in self._inventory.items():
            if key.startswith(prefix):
                matches.append(record)

        # Rank by:
        # 1. frequency (count)
        # 2. recency (last_used)
        matches.sort(
            key=lambda r: (r["count"], r["last_used"]),
            reverse=True
        )

        suggestions = [r["name"] for r in matches[:limit]]

        return {
            "suggestions": suggestions,
            "needs_confirmation": True
        }

    # ---------------- DEBUG / VISIBILITY ---------------- #

    def get_inventory_snapshot(self) -> List[Dict]:
        """
        Returns current inventory memory (for debugging / admin).
        """
        return list(self._inventory.values())
