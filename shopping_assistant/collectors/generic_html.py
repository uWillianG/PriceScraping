from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus, urljoin

from shopping_assistant.collectors.base import BaseCollector, CollectorBlocked, CollectorError
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class GenericHtmlCollector(BaseCollector):
    search_url_template: str
    search_encoding: str = "quote_plus"
    card_selector: str
    link_selector: str
    wait_selector: str
    base_url: str
    debug_file: str

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        url = self.build_search_url(query)
        try:
            html = await self.get_text(
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                check_robots=True,
            )
            self.raise_if_blocked_page(html)
            offers = self.extract_offers(html, category)
            if offers:
                return offers
        except (CollectorBlocked, CollectorError) as exc:
            self.logger.info(
                "%s static request failed; trying Playwright fallback: %s",
                self.store_name,
                exc,
            )

        rendered = await self.get_rendered_html(
            url,
            wait_selector=self.wait_selector,
            check_robots=True,
            debug_name=self.debug_file,
        )
        self.raise_if_blocked_page(rendered)
        offers = self.extract_offers(rendered, category)
        if offers:
            return offers

        self.save_debug_html(rendered)
        raise CollectorError(
            f"{self.store_name} page loaded, but no product offers were found. "
            f"Saved debug HTML to data/debug/{self.debug_file}"
        )

    def raise_if_blocked_page(self, html: str) -> None:
        lower = html.lower()
        blocked_markers = [
            "akamai-bot",
            "customdeny",
            "não é possível acessar a página",
            "nao e possivel acessar a pagina",
            "ops! algo deu errado",
            "anti_crawler",
            "anticrawler",
            "captcha",
            "robô",
            "robo",
        ]
        if any(marker in lower for marker in blocked_markers):
            self.save_debug_html(html)
            raise CollectorBlocked(
                f"{self.store_name} blocked automated access or served an anti-bot "
                f"page. Saved debug HTML to data/debug/{self.debug_file}. "
                "Use an official/affiliate API endpoint in .env for reliable results."
            )

    def build_search_url(self, query: str) -> str:
        clean = query.strip().lower()
        if self.search_encoding == "slug":
            encoded = quote(re.sub(r"\s+", "-", clean))
        else:
            encoded = quote_plus(clean)
        return self.search_url_template.format(query=encoded)

    def extract_offers(self, html: str, category: str | None) -> list[ProductOffer]:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise CollectorError("beautifulsoup4 is required for HTML scraping.") from exc

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(self.card_selector)
        offers = [
            offer
            for card in cards[:30]
            if (offer := self.normalize_card(card, category)) is not None
        ]
        if offers:
            return self.dedupe(offers)

        links = soup.select(self.link_selector)
        return self.dedupe(self.extract_from_links(links, category))

    def normalize_card(self, card: Any, category: str | None) -> ProductOffer | None:
        link = card if getattr(card, "name", None) == "a" else card.select_one(self.link_selector)
        if link is None:
            return None
        title = self.extract_title(link, card)
        url = self.absolute_url(link.get("href"))
        current = self.extract_price(card)
        if not title or not url or current is None:
            return None
        original = self.extract_original_price(card)
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
            product_id=self.extract_product_id(url),
            category=category,
            image_url=image_url,
        )

    def extract_from_links(self, links: list[Any], category: str | None) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        for link in links[:60]:
            card = link
            for _ in range(7):
                if card.parent is None:
                    break
                card = card.parent
                if card.name in {"li", "article"}:
                    break
            offer = self.normalize_card(card, category)
            if offer:
                offers.append(offer)
            if len(offers) >= 20:
                break
        return offers

    def extract_title(self, link: Any, card: Any) -> str:
        title = link.get("title") or link.get("aria-label") or link.get_text(" ", strip=True)
        if title:
            return title.strip()
        heading = card.select_one("h2, h3, [data-testid*='title'], [class*='title']")
        return heading.get_text(" ", strip=True) if heading else ""

    def extract_price(self, card: Any):
        meta = card.select_one("meta[itemprop='price'], meta[property='product:price:amount']")
        if meta and meta.get("content"):
            return to_decimal(meta.get("content"))

        text = card.get_text(" ", strip=True)
        matches = re.findall(r"R\$\s*([\d\.]+)(?:,(\d{2}))?", text)
        if not matches:
            matches = re.findall(r"([\d\.]+)\s*reais(?:\s*com\s*(\d{2})\s*centavos)?", text)
        for fraction, cents in matches:
            value = to_decimal(self.join_price_parts(fraction, cents))
            if value is not None and value > 0:
                return value
        return None

    def extract_original_price(self, card: Any):
        previous = card.select_one(
            "[class*='old'], [class*='original'], [class*='previous'], "
            "[data-testid*='original'], s"
        )
        if previous is None:
            return None
        return self.extract_price(previous)

    def absolute_url(self, href: str | None) -> str | None:
        if not href:
            return None
        return urljoin(self.base_url, href)

    def extract_product_id(self, url: str) -> str | None:
        match = re.search(r"([A-Z]{2,5}-?\d{4,}|\d{5,})", url)
        return match.group(1).replace("-", "") if match else None

    @staticmethod
    def join_price_parts(fraction: str, cents: str | None = None) -> str:
        clean_fraction = re.sub(r"[^\d]", "", fraction)
        clean_cents = re.sub(r"[^\d]", "", cents or "")
        return f"{clean_fraction}.{clean_cents[:2]}" if clean_cents else clean_fraction

    @staticmethod
    def dedupe(offers: list[ProductOffer]) -> list[ProductOffer]:
        seen: set[str] = set()
        unique: list[ProductOffer] = []
        for offer in offers:
            key = offer.url
            if key in seen:
                continue
            seen.add(key)
            unique.append(offer)
        return unique[:20]

    def save_debug_html(self, html: str) -> None:
        path = Path("data/debug") / self.debug_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
