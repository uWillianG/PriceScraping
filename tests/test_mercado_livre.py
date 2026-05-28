from decimal import Decimal

from config import settings
from shopping_assistant.collectors.mercado_livre import MercadoLivreCollector


def test_mercado_livre_normalizes_api_item():
    item = {
        "id": "MLB123",
        "title": "Geladeira Frost Free",
        "price": 2500,
        "original_price": 3000,
        "permalink": "https://produto.mercadolivre.com.br/MLB123",
        "thumbnail": "https://image.test/1.jpg",
        "available_quantity": 5,
    }

    offer = MercadoLivreCollector(settings)._normalize_item(item, "appliances")

    assert offer is not None
    assert offer.store == "Mercado Livre"
    assert offer.current_price == Decimal("2500.00")
    assert offer.discount_percent == Decimal("16.67")
    assert offer.category == "appliances"
