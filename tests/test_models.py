from decimal import Decimal

from shopping_assistant.models import ProductOffer, compute_discount_percent


def test_discount_percent_is_computed():
    assert compute_discount_percent(Decimal("80"), Decimal("100")) == Decimal("20.00")


def test_product_offer_quantizes_prices_and_discount():
    offer = ProductOffer(
        store="Test Store",
        title="Sofa",
        current_price=Decimal("99.999"),
        original_price=Decimal("199.999"),
        discount_percent=None,
        url="https://example.com/sofa",
    )

    assert offer.current_price == Decimal("100.00")
    assert offer.original_price == Decimal("200.00")
    assert offer.discount_percent == Decimal("50.00")
