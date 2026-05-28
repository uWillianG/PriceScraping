from decimal import Decimal

import pytest

from shopping_assistant.collectors.base import BaseCollector
from shopping_assistant.models import ProductOffer
from shopping_assistant.services.comparison import PriceComparisonEngine


class StubCollector(BaseCollector):
    def __init__(self, store_name, offers):
        self.store_name = store_name
        self.offers = offers

    async def search(self, query, category=None):
        return self.offers


@pytest.mark.asyncio
async def test_search_all_ranks_by_price():
    offers = [
        ProductOffer("A", "Expensive", Decimal("200"), None, None, "https://a.test"),
        ProductOffer("B", "Cheap", Decimal("100"), None, None, "https://b.test"),
    ]
    engine = PriceComparisonEngine([StubCollector("stub", offers)])

    result = await engine.search_all("mesa")

    assert [offer.title for offer in result.ranked_offers] == ["Cheap", "Expensive"]


def test_best_by_category_picks_lowest_price():
    offers = [
        ProductOffer("A", "Sofa A", Decimal("900"), None, None, "https://a.test", category="furniture"),
        ProductOffer("B", "Sofa B", Decimal("800"), None, None, "https://b.test", category="furniture"),
    ]

    best = PriceComparisonEngine.best_by_category(offers)

    assert best["furniture"].title == "Sofa B"
