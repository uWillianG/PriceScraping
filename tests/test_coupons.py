from decimal import Decimal

from config import settings
from shopping_assistant.models import Coupon, ProductOffer
from shopping_assistant.services.coupons import MercadoLivreCouponService


def test_coupon_matches_offer_by_keyword_and_min_purchase():
    service = MercadoLivreCouponService(settings)
    coupon = Coupon(
        store="Mercado Livre",
        title="R$ 50 OFF",
        description="Cupom em geladeiras",
        url="https://www.mercadolivre.com.br/cupons/filter",
        discount_text="R$ 50 OFF",
        min_purchase=Decimal("500"),
        category="appliances",
        keywords=["geladeira"],
    )
    offer = ProductOffer(
        store="Mercado Livre",
        title="Geladeira Frost Free",
        current_price=Decimal("2500"),
        original_price=None,
        discount_percent=None,
        url="https://produto.mercadolivre.com.br/MLB-123",
        category="appliances",
    )

    assert service.coupon_matches_offer(coupon, offer, "geladeira", "appliances")


def test_coupon_does_not_match_below_min_purchase():
    service = MercadoLivreCouponService(settings)
    coupon = Coupon(
        store="Mercado Livre",
        title="R$ 50 OFF",
        description="Cupom em geladeiras",
        url="https://www.mercadolivre.com.br/cupons/filter",
        min_purchase=Decimal("500"),
        keywords=["geladeira"],
    )
    offer = ProductOffer(
        store="Mercado Livre",
        title="Geladeira pequena",
        current_price=Decimal("300"),
        original_price=None,
        discount_percent=None,
        url="https://produto.mercadolivre.com.br/MLB-123",
    )

    assert not service.coupon_matches_offer(coupon, offer, "geladeira", None)
