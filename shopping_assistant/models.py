from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import StrEnum


MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


class AlertRuleType(StrEnum):
    TARGET_PRICE = "target_price"
    DISCOUNT_PERCENT = "discount_percent"
    HISTORICAL_LOW = "historical_low"


def to_decimal(value: object, default: Decimal | None = None) -> Decimal | None:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return default


def compute_discount_percent(
    current_price: Decimal,
    original_price: Decimal | None,
) -> Decimal | None:
    if original_price is None or original_price <= 0 or current_price >= original_price:
        return None
    discount = ((original_price - current_price) / original_price) * Decimal("100")
    return discount.quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


@dataclass(slots=True)
class ProductOffer:
    store: str
    title: str
    current_price: Decimal
    original_price: Decimal | None
    discount_percent: Decimal | None
    url: str
    product_id: str | None = None
    category: str | None = None
    image_url: str | None = None
    available: bool = True
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.current_price = Decimal(str(self.current_price)).quantize(MONEY_QUANT)
        if self.original_price is not None:
            self.original_price = Decimal(str(self.original_price)).quantize(MONEY_QUANT)
        if self.discount_percent is None:
            self.discount_percent = compute_discount_percent(
                self.current_price, self.original_price
            )


@dataclass(slots=True)
class TrackedProduct:
    query: str
    category: str | None = None
    target_price: Decimal | None = None
    active: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class PriceSnapshot:
    store: str
    title: str
    current_price: Decimal
    original_price: Decimal | None
    discount_percent: Decimal | None
    url: str
    product_id: str | None = None
    category: str | None = None
    tracked_product_id: int | None = None
    image_url: str | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None


@dataclass(slots=True)
class AlertRule:
    rule_type: AlertRuleType
    threshold: Decimal | None = None
    tracked_product_id: int | None = None
    active: bool = True
    id: int | None = None


@dataclass(slots=True)
class DealAlert:
    rule_type: AlertRuleType
    offer: ProductOffer
    message: str
    threshold: Decimal | None = None
    historical_price: Decimal | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class SearchResult:
    query: str
    category: str | None
    ranked_offers: list[ProductOffer]
    best_by_category: dict[str, ProductOffer]
    errors: dict[str, str]
