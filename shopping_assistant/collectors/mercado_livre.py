from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from shopping_assistant.collectors.base import BaseCollector, CollectorBlocked
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class MercadoLivreCollector(BaseCollector):
    store_name = "Mercado Livre"
    search_url = "https://api.mercadolibre.com/sites/MLB/search"
    html_search_url = "https://lista.mercadolivre.com.br/{query}"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        try:
            payload = await self.get_json(
                self.search_url,
                params={"q": query, "limit": 20},
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                    "Referer": "https://www.mercadolivre.com.br/",
                },
                check_robots=False,
            )
            return [
                offer
                for item in payload.get("results", [])
                if (offer := self._normalize_item(item, category)) is not None
            ]
        except CollectorBlocked as exc:
            self.logger.warning("Mercado Livre API blocked; trying HTML fallback: %s", exc)
            return await self._search_html(query, category)

    def _normalize_item(
        self, item: dict[str, Any], category: str | None
    ) -> ProductOffer | None:
        title = item.get("title")
        url = item.get("permalink")
        current = to_decimal(item.get("price"))
        if not title or not url or current is None:
            return None

        original = to_decimal(item.get("original_price"))
        discount = compute_discount_percent(current, original)
        thumbnail = item.get("thumbnail") or item.get("secure_thumbnail")
        return ProductOffer(
            store=self.store_name,
            title=title,
            current_price=current,
            original_price=original,
            discount_percent=discount,
            url=url,
            product_id=item.get("id"),
            category=category,
            image_url=thumbnail,
            available=item.get("available_quantity", 1) != 0,
        )

    async def _search_html(
        self, query: str, category: str | None = None
    ) -> list[ProductOffer]:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise CollectorBlocked(
                "Mercado Livre API was blocked and beautifulsoup4 is not installed "
                "for the HTML fallback."
            ) from exc

        url = self.html_search_url.format(query=quote_plus(query))
        html = await self.get_text(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Referer": "https://www.mercadolivre.com.br/",
            },
            check_robots=True,
        )
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(
            "li.ui-search-layout__item, div.ui-search-result, div.poly-card, "
            "section.ui-search-results li"
        )
        offers = [
            offer
            for card in cards[:20]
            if (offer := self._normalize_html_card(card, category)) is not None
        ]
        return offers

    def _normalize_html_card(self, card: Any, category: str | None) -> ProductOffer | None:
        link = card.select_one(
            "a.poly-component__title, a.ui-search-link, "
            "h3.poly-component__title-wrapper a, a[href*='produto.mercadolivre.com.br']"
        )
        if link is None:
            return None

        title = link.get_text(" ", strip=True)
        url = link.get("href")
        if not title or not url:
            return None

        current = self._extract_price(card)
        if current is None:
            return None

        original = self._extract_original_price(card)
        image = card.select_one("img")
        image_url = None
        if image is not None:
            image_url = image.get("data-src") or image.get("src")

        return ProductOffer(
            store=self.store_name,
            title=title,
            current_price=current,
            original_price=original,
            discount_percent=compute_discount_percent(current, original),
            url=url,
            product_id=self._extract_product_id(url),
            category=category,
            image_url=image_url,
        )

    def _extract_price(self, card: Any):
        meta_price = card.select_one("meta[itemprop='price']")
        if meta_price and meta_price.get("content"):
            return to_decimal(meta_price.get("content"))

        amount = card.select_one(
            ".andes-money-amount:not(.andes-money-amount--previous) "
            ".andes-money-amount__fraction"
        )
        if amount:
            cents = card.select_one(
                ".andes-money-amount:not(.andes-money-amount--previous) "
                ".andes-money-amount__cents"
            )
            return to_decimal(self._join_price_parts(amount.get_text(), cents.get_text() if cents else None))

        text = card.get_text(" ", strip=True)
        match = re.search(r"R\$\s*([\d\.]+)(?:,(\d{2}))?", text)
        if not match:
            return None
        return to_decimal(self._join_price_parts(match.group(1), match.group(2)))

    def _extract_original_price(self, card: Any):
        previous = card.select_one(
            ".andes-money-amount--previous .andes-money-amount__fraction, "
            ".ui-search-price__original-value .andes-money-amount__fraction"
        )
        if previous is None:
            return None
        cents = previous.find_next(class_="andes-money-amount__cents")
        return to_decimal(self._join_price_parts(previous.get_text(), cents.get_text() if cents else None))

    @staticmethod
    def _join_price_parts(fraction: str, cents: str | None = None) -> str:
        clean_fraction = re.sub(r"[^\d]", "", fraction)
        clean_cents = re.sub(r"[^\d]", "", cents or "")
        if clean_cents:
            return f"{clean_fraction}.{clean_cents[:2]}"
        return clean_fraction

    @staticmethod
    def _extract_product_id(url: str) -> str | None:
        match = re.search(r"(MLB-?\d+)", url)
        if not match:
            return None
        return match.group(1).replace("-", "")
