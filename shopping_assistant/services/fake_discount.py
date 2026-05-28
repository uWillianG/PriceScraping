from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from shopping_assistant.models import PriceSnapshot, ProductOffer


@dataclass(slots=True)
class FakeDiscountFinding:
    offer: ProductOffer
    historical_average: Decimal | None
    historical_low: Decimal | None
    original_price_inflation_percent: Decimal | None
    suspicious: bool
    reason: str


class FakeDiscountDetector:
    def __init__(self, inflation_threshold_percent: Decimal = Decimal("15")) -> None:
        self.inflation_threshold_percent = inflation_threshold_percent

    def analyze(
        self, offer: ProductOffer, history: list[PriceSnapshot]
    ) -> FakeDiscountFinding:
        if not history:
            return FakeDiscountFinding(
                offer=offer,
                historical_average=None,
                historical_low=None,
                original_price_inflation_percent=None,
                suspicious=False,
                reason="No history yet.",
            )

        prices = [snapshot.current_price for snapshot in history]
        historical_average = (sum(prices) / Decimal(len(prices))).quantize(Decimal("0.01"))
        historical_low = min(prices)

        if offer.original_price is None:
            return FakeDiscountFinding(
                offer=offer,
                historical_average=historical_average,
                historical_low=historical_low,
                original_price_inflation_percent=None,
                suspicious=False,
                reason="No original price shown.",
            )

        inflation = (
            ((offer.original_price - historical_average) / historical_average)
            * Decimal("100")
        ).quantize(Decimal("0.01"))
        suspicious = inflation >= self.inflation_threshold_percent
        reason = (
            "Shown original price is above historical average."
            if suspicious
            else "Shown original price is consistent with history."
        )
        return FakeDiscountFinding(
            offer=offer,
            historical_average=historical_average,
            historical_low=historical_low,
            original_price_inflation_percent=inflation,
            suspicious=suspicious,
            reason=reason,
        )
