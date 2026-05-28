from __future__ import annotations

from shopping_assistant.collectors.base import BaseCollector
from shopping_assistant.models import ProductOffer


class ShopeeCollector(BaseCollector):
    store_name = "Shopee Brasil"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if not self.settings.shopee_affiliate_endpoint:
            self.logger.info("Shopee affiliate/open API endpoint is not configured")
            return []

        data = await self.get_json(
            self.settings.shopee_affiliate_endpoint,
            params={"keyword": query},
            headers=self._headers(),
            check_robots=False,
        )
        return self._normalize_items(data, category)

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.settings.shopee_partner_id:
            headers["X-Shopee-Partner-Id"] = self.settings.shopee_partner_id
        return headers

    def _normalize_items(self, data: dict, category: str | None) -> list[ProductOffer]:
        # Shopee APIs vary by partner product. Keep the adapter conservative until
        # the configured endpoint's response shape is known.
        self.logger.warning("Shopee endpoint configured, but response mapper is generic")
        return []
