from datetime import datetime, timezone
from decimal import Decimal

from shopping_assistant.models import PriceSnapshot, ProductOffer
from shopping_assistant.services.fake_discount import FakeDiscountDetector


def snapshot(price):
    return PriceSnapshot(
        store="Store",
        title="TV",
        current_price=Decimal(price),
        original_price=None,
        discount_percent=None,
        url="https://example.com/tv",
        collected_at=datetime.now(timezone.utc),
    )


def test_fake_discount_detector_flags_inflated_original_price():
    offer = ProductOffer(
        store="Store",
        title="TV",
        current_price=Decimal("900"),
        original_price=Decimal("1400"),
        discount_percent=None,
        url="https://example.com/tv",
    )
    detector = FakeDiscountDetector(inflation_threshold_percent=Decimal("15"))

    finding = detector.analyze(offer, [snapshot("1000"), snapshot("1000")])

    assert finding.suspicious is True
    assert finding.original_price_inflation_percent == Decimal("40.00")


def test_fake_discount_detector_handles_no_history():
    offer = ProductOffer("Store", "Lamp", Decimal("50"), None, None, "https://example.com")

    finding = FakeDiscountDetector().analyze(offer, [])

    assert finding.suspicious is False
    assert finding.historical_average is None
