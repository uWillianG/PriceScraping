from decimal import Decimal

from config import settings
from shopping_assistant.models import ProductOffer
from shopping_assistant.services.emailer import EmailNotifier


def test_email_html_contains_deal_data():
    offer = ProductOffer(
        "Mercado Livre",
        "Geladeira",
        Decimal("2500"),
        Decimal("3000"),
        None,
        "https://example.com",
    )

    html = EmailNotifier(settings).render_deals_html([offer])

    assert "Geladeira" in html
    assert "Mercado Livre" in html
    assert "2500.00" in html
