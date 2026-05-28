from decimal import Decimal

from config import settings
from shopping_assistant.collectors.amazon import AmazonCollector


def test_amazon_paapi_response_normalization():
    data = {
        "SearchResult": {
            "Items": [
                {
                    "ASIN": "B00TESTE",
                    "DetailPageURL": "https://www.amazon.com.br/dp/B00TESTE",
                    "ItemInfo": {"Title": {"DisplayValue": "Micro-ondas Midea"}},
                    "Images": {
                        "Primary": {
                            "Medium": {"URL": "https://example.com/image.jpg"}
                        }
                    },
                    "Offers": {
                        "Listings": [
                            {
                                "Price": {"Amount": 499.9},
                                "SavingBasis": {"Amount": 699.9},
                            }
                        ]
                    },
                }
            ]
        }
    }

    offers = AmazonCollector(settings)._normalize_paapi_response(data, "appliances")

    assert len(offers) == 1
    assert offers[0].store == "Amazon Brasil"
    assert offers[0].current_price == Decimal("499.90")
    assert offers[0].original_price == Decimal("699.90")
