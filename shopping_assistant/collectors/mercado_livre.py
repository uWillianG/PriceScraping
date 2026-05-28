from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from shopping_assistant.collectors.base import BaseCollector, CollectorBlocked, CollectorError
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class MercadoLivreCollector(BaseCollector):
    store_name = "Mercado Livre"
    search_url = "https://api.mercadolibre.com/sites/MLB/search"
    html_search_url = "https://lista.mercadolivre.com.br/{query}"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if not self.settings.mercado_livre_use_api:
            return await self._search_html(query, category)

        try:
            headers = {
                "Accept": "application/json",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Referer": "https://www.mercadolivre.com.br/",
            }
            if self.settings.mercado_livre_access_token:
                headers["Authorization"] = (
                    f"Bearer {self.settings.mercado_livre_access_token}"
                )

            payload = await self.get_json(
                self.search_url,
                params={"q": query, "limit": 20},
                headers=headers,
                check_robots=False,
            )
            return [
                offer
                for item in payload.get("results", [])
                if (offer := self._normalize_item(item, category)) is not None
            ]
        except CollectorBlocked as exc:
            self.logger.info("Mercado Livre API blocked; trying HTML fallback: %s", exc)
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

        slug = re.sub(r"\s+", "-", query.strip().lower())
        url = self.html_search_url.format(query=quote(slug))
        html = await self.get_text(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
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
        if not offers:
            offers = self._extract_offers_from_links(soup, category)
        if not offers:
            offers = await self._search_with_playwright(url, category)
        return offers

    async def _search_with_playwright(
        self, url: str, category: str | None = None
    ) -> list[ProductOffer]:
        return await asyncio.to_thread(self._search_with_playwright_sync, url, category)

    def _search_with_playwright_sync(
        self, url: str, category: str | None = None
    ) -> list[ProductOffer]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise CollectorError(
                "Mercado Livre loaded without static product offers. Install Playwright "
                "to render JavaScript results: pip install playwright && "
                "python -m playwright install chromium"
            ) from exc

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=self.settings.user_agent,
                    locale="pt-BR",
                    viewport={"width": 1366, "height": 900},
                )
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
                    page.wait_for_selector(
                        "li.ui-search-layout__item, div.poly-card, a[href*='MLB']",
                        timeout=15000,
                    )
                    html = page.content()
                finally:
                    browser.close()
        except NotImplementedError as exc:
            raise CollectorError(
                "Playwright could not start Chromium in this Python/Windows event loop. "
                "Try running with Python 3.12 or 3.13, or use the API mode with a "
                "Mercado Livre access token."
            ) from exc

        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise CollectorError("beautifulsoup4 is required to parse rendered HTML.") from exc

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
        if not offers:
            offers = self._extract_offers_from_links(soup, category)
        if not offers:
            self._save_debug_html(html)
            title = soup.title.get_text(" ", strip=True) if soup.title else "no page title"
            raise CollectorError(
                "Mercado Livre rendered page loaded, but no product offers were "
                f"found. Page title: {title}. Saved debug HTML to data/debug/mercado_livre_last.html"
            )
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

    def _extract_offers_from_links(
        self, soup: Any, category: str | None
    ) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        seen_urls: set[str] = set()
        product_links = soup.select(
            "a[href*='produto.mercadolivre.com.br/MLB'], "
            "a[href*='mercadolivre.com.br/p/MLB'], "
            "a[href*='mercadolivre.com.br/MLB-']"
        )
        for link in product_links:
            url = link.get("href")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            card = link
            for _ in range(6):
                if card.parent is None:
                    break
                card = card.parent
                if card.name in {"li", "article"} or "poly-card" in card.get("class", []):
                    break

            title = (
                link.get("title")
                or link.get("aria-label")
                or link.get_text(" ", strip=True)
            )
            if not title:
                heading = card.select_one("h2, h3, .poly-component__title")
                title = heading.get_text(" ", strip=True) if heading else ""
            current = self._extract_price(card)
            if not title or current is None:
                continue

            image = card.select_one("img")
            image_url = None
            if image is not None:
                image_url = image.get("data-src") or image.get("src")

            original = self._extract_original_price(card)
            offers.append(
                ProductOffer(
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
            )
            if len(offers) >= 20:
                break
        return offers

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
            match = re.search(r"([\d\.]+)\s*reais(?:\s*com\s*(\d{2})\s*centavos)?", text)
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

    @staticmethod
    def _save_debug_html(html: str) -> None:
        debug_path = Path("data/debug/mercado_livre_last.html")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(html, encoding="utf-8")
