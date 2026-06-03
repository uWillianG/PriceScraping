from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

from shopping_assistant.collectors.generic_html import GenericHtmlCollector
from shopping_assistant.models import ProductOffer, compute_discount_percent


class GoogleShoppingCollector(GenericHtmlCollector):
    store_name = "Google Shopping"
    base_url = "https://www.google.com"
    search_url_template = "https://www.google.com/search?tbm=shop&hl=pt-BR&gl=br&q={query}"
    search_encoding = "quote_plus"
    card_selector = (
        "div.sh-dgr__grid-result, div.sh-dlr__list-result, div[data-docid], "
        "div[jscontroller][data-hveid]"
    )
    link_selector = "a[href*='/shopping/product/'], a[href*='/url?'], a[href^='http']"
    wait_selector = (
        "div.sh-dgr__grid-result, div.sh-dlr__list-result, "
        "a[href*='/shopping/product/'], a[href*='/url?']"
    )
    debug_file = "google_shopping_last.html"

    def build_search_url(self, query: str) -> str:
        return self.search_url_template.format(query=quote_plus(query.strip()))

    def raise_if_blocked_page(self, html: str) -> None:
        lower = html.lower()
        blocked_markers = [
            "our systems have detected unusual traffic",
            "detected unusual traffic",
            "/sorry/",
            "recaptcha",
            "captcha",
            "consent.google",
            "before you continue to google",
            "antes de continuar para o google",
        ]
        if any(marker in lower for marker in blocked_markers):
            self.save_debug_html(html)
            from shopping_assistant.collectors.base import CollectorBlocked

            raise CollectorBlocked(
                "Google Shopping served a consent, CAPTCHA, or unusual-traffic page. "
                f"Saved debug HTML to data/debug/{self.debug_file}."
            )

    def normalize_card(self, card: Any, category: str | None) -> ProductOffer | None:
        title = self._extract_google_title(card)
        current = self.extract_price(card)
        link = card.select_one(self.link_selector)
        url = self.absolute_url(link.get("href") if link else None)
        if not title or current is None or not url:
            return None

        original = self.extract_original_price(card)
        image = card.select_one("img")
        image_url = None
        if image is not None:
            image_url = image.get("data-src") or image.get("src")

        merchant = self._extract_merchant(card)
        return ProductOffer(
            store=f"Google Shopping - {merchant}" if merchant else self.store_name,
            title=title,
            current_price=current,
            original_price=original,
            discount_percent=compute_discount_percent(current, original),
            url=url,
            product_id=self.extract_product_id(url),
            category=category,
            image_url=image_url,
        )

    def absolute_url(self, href: str | None) -> str | None:
        if not href:
            return None
        if href.startswith("/url?"):
            query = parse_qs(urlparse(href).query)
            target = query.get("q") or query.get("url")
            if target:
                return unquote(target[0])
        if href.startswith("/aclk?"):
            query = parse_qs(urlparse(href).query)
            target = query.get("adurl")
            if target:
                return unquote(target[0])
        return urljoin(self.base_url, href)

    def _extract_google_title(self, card: Any) -> str:
        selectors = [
            "h3",
            ".tAxDx",
            ".EI11Pd",
            ".sh-np__product-title",
            "[role='heading']",
            "a[title]",
        ]
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                title = node.get("title") or node.get_text(" ", strip=True)
                if title:
                    return title.strip()
        return ""

    def _extract_merchant(self, card: Any) -> str | None:
        selectors = [
            ".aULzUe",
            ".IuHnof",
            ".sh-np__seller-container",
            "[class*='merchant']",
            "[class*='seller']",
        ]
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                text = node.get_text(" ", strip=True)
                if text and "R$" not in text:
                    return text
        return None
