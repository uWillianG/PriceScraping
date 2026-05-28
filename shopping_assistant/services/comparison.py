from __future__ import annotations

import asyncio

from shopping_assistant.collectors.base import BaseCollector
from shopping_assistant.models import ProductOffer, SearchResult


class PriceComparisonEngine:
    def __init__(self, collectors: list[BaseCollector]) -> None:
        self.collectors = collectors

    async def search_all(self, query: str, category: str | None = None) -> SearchResult:
        results = await asyncio.gather(
            *(collector.search(query, category=category) for collector in self.collectors),
            return_exceptions=True,
        )
        offers: list[ProductOffer] = []
        errors: dict[str, str] = {}

        for collector, result in zip(self.collectors, results, strict=True):
            if isinstance(result, Exception):
                errors[collector.store_name] = str(result)
                continue
            offers.extend(result)

        ranked = sorted(
            (offer for offer in offers if offer.available),
            key=lambda offer: offer.current_price,
        )
        return SearchResult(
            query=query,
            category=category,
            ranked_offers=ranked,
            best_by_category=self.best_by_category(ranked),
            errors=errors,
        )

    @staticmethod
    def best_by_category(offers: list[ProductOffer]) -> dict[str, ProductOffer]:
        best: dict[str, ProductOffer] = {}
        for offer in offers:
            key = offer.category or "uncategorized"
            if key not in best or offer.current_price < best[key].current_price:
                best[key] = offer
        return best
