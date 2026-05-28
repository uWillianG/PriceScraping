from __future__ import annotations

from shopping_assistant.db.repositories import PriceRepository
from shopping_assistant.models import ProductOffer


class PriceHistoryTracker:
    def __init__(self, repository: PriceRepository) -> None:
        self.repository = repository

    def save_snapshots(
        self, offers: list[ProductOffer], tracked_product_id: int | None = None
    ) -> list[int]:
        return [
            self.repository.save_offer(offer, tracked_product_id=tracked_product_id)
            for offer in offers
        ]
