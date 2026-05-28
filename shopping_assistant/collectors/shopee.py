from __future__ import annotations

from shopping_assistant.collectors.generic_html import GenericHtmlCollector
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class ShopeeCollector(GenericHtmlCollector):
    store_name = "Shopee Brasil"
    base_url = "https://shopee.com.br"
    search_url_template = "https://shopee.com.br/search?keyword={query}"
    search_encoding = "quote_plus"
    card_selector = "li, div[data-sqe='item'], div[class*='shop-search-result-view'] a"
    link_selector = "a[href*='-i.'], a[href*='shopee.com.br/']"
    wait_selector = "a[href*='-i.'], div[data-sqe='item']"
    debug_file = "shopee_last.html"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if not self.settings.shopee_affiliate_endpoint:
            return await super().search(query, category)

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
        raw_items = data.get("items") or data.get("results") or data.get("products") or []
        offers: list[ProductOffer] = []
        for item in raw_items:
            title = item.get("title") or item.get("name") or item.get("item_name")
            url = item.get("url") or item.get("link") or item.get("product_link")
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
                    product_id=str(item.get("id") or item.get("item_id") or "") or None,
                    category=category,
                    image_url=item.get("image_url") or item.get("image"),
                )
            )
        return offers
