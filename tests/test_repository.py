from decimal import Decimal

from shopping_assistant.db.repositories import PriceRepository
from shopping_assistant.models import ProductOffer, TrackedProduct


def test_repository_inserts_and_reads_snapshot(tmp_path):
    repository = PriceRepository(tmp_path / "prices.db")
    tracked_id = repository.add_tracked_product(
        TrackedProduct(query="mesa jantar", category="furniture")
    )
    offer = ProductOffer(
        store="Store",
        title="Mesa",
        current_price=Decimal("500"),
        original_price=Decimal("650"),
        discount_percent=None,
        url="https://example.com/mesa",
        product_id="123",
        category="furniture",
    )

    repository.save_offer(offer, tracked_product_id=tracked_id)
    snapshots = repository.history_for_tracked_product(tracked_id)

    assert len(snapshots) == 1
    assert snapshots[0].current_price == Decimal("500.00")
