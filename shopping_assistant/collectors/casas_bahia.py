from __future__ import annotations

from shopping_assistant.collectors.base import BaseCollector
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class CasasBahiaCollector(BaseCollector):
    store_name = "Casas Bahia"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if not self.settings.casas_bahia_search_endpoint:
            self.logger.info("Casas Bahia search endpoint is not configured")
            return []

        data = await self.get_json(
            self.settings.casas_bahia_search_endpoint,
            params={"q": query},
            headers=self._headers(),
            check_robots=False,
        )
        return self._normalize_items(data, category)

    def _headers(self) -> dict[str, str]:
        if not self.settings.casas_bahia_api_token:
            return {}
        return {"Authorization": f"Bearer {self.settings.casas_bahia_api_token}"}

    def _normalize_items(self, data: dict, category: str | None) -> list[ProductOffer]:
        raw_items = data.get("items") or data.get("results") or data.get("products") or []
        offers: list[ProductOffer] = []
        for item in raw_items:
            title = item.get("title") or item.get("name")
            url = item.get("url") or item.get("link")
            current = to_decimal(item.get("price") or item.get("current_price"))
            if not title or not url or current is None:
                continue
            original = to_decimal(item.get("original_price") or item.get("list_price"))
            offers.append(
                ProductOffer(
                    store=self.store_name,
                    title=title,
                    current_price=current,
                    original_price=original,
                    discount_percent=compute_discount_percent(current, original),
                    url=url,
                    product_id=str(item.get("id") or item.get("sku") or "") or None,
                    category=category,
                    image_url=item.get("image_url") or item.get("image"),
                )
            )
        return offers
