from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import aiohttp

from config import Settings
from shopping_assistant.models import Coupon, ProductOffer, to_decimal


class MercadoLivreCouponService:
    coupon_url = "https://www.mercadolivre.com.br/cupons/filter"

    def __init__(
        self,
        settings: Settings,
        local_coupon_path: Path | str = "coupons/mercado_livre.json",
    ) -> None:
        self.settings = settings
        self.local_coupon_path = Path(local_coupon_path)

    async def coupons_for_offers(
        self,
        offers: list[ProductOffer],
        *,
        query: str,
        category: str | None,
    ) -> dict[str, list[Coupon]]:
        coupons = self.load_local_coupons()
        coupons.extend(await self.fetch_public_coupons())
        matched: dict[str, list[Coupon]] = {}
        for offer in offers:
            if offer.store != "Mercado Livre":
                continue
            offer_matches = [
                coupon
                for coupon in coupons
                if self.coupon_matches_offer(coupon, offer, query, category)
            ]
            if offer_matches:
                matched[offer.url] = offer_matches[:3]
        return matched

    def load_local_coupons(self) -> list[Coupon]:
        if not self.local_coupon_path.exists():
            return []
        data = json.loads(self.local_coupon_path.read_text(encoding="utf-8"))
        return [self._coupon_from_dict(item) for item in data]

    async def fetch_public_coupons(self) -> list[Coupon]:
        headers = {
            "User-Agent": self.settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        try:
            timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.coupon_url, headers=headers) as response:
                    if response.status >= 400:
                        return []
                    html = await response.text()
        except (aiohttp.ClientError, TimeoutError):
            return []
        return self.parse_public_coupon_page(html)

    def parse_public_coupon_page(self, html: str) -> list[Coupon]:
        lower = html.lower()
        if "seguridad" in lower or "captcha" in lower or "unusual traffic" in lower:
            self.save_debug_html(html)
            return []
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        soup = BeautifulSoup(html, "html.parser")
        text_blocks = [
            block.get_text(" ", strip=True)
            for block in soup.select("article, section, li, div")
        ]
        coupons: list[Coupon] = []
        seen: set[str] = set()
        for text in text_blocks:
            if not self.looks_like_coupon(text):
                continue
            key = text[:120]
            if key in seen:
                continue
            seen.add(key)
            coupons.append(self.coupon_from_text(text))
            if len(coupons) >= 20:
                break
        return coupons

    def coupon_matches_offer(
        self,
        coupon: Coupon,
        offer: ProductOffer,
        query: str,
        category: str | None,
    ) -> bool:
        if coupon.store != "Mercado Livre":
            return False
        if coupon.min_purchase and offer.current_price < coupon.min_purchase:
            return False
        if coupon.category and category and coupon.category != category:
            return False
        if not coupon.keywords:
            return True
        haystack = f"{offer.title} {query} {category or ''}".lower()
        return any(keyword.lower() in haystack for keyword in coupon.keywords)

    def coupon_from_text(self, text: str) -> Coupon:
        discount = self.extract_discount_text(text)
        code = self.extract_code(text)
        min_purchase = self.extract_min_purchase(text)
        return Coupon(
            store="Mercado Livre",
            title=discount or "Cupom Mercado Livre",
            description=text[:260],
            url=self.coupon_url,
            code=code,
            discount_text=discount,
            min_purchase=min_purchase,
        )

    @staticmethod
    def looks_like_coupon(text: str) -> bool:
        lower = text.lower()
        return "cupom" in lower and ("r$" in lower or "%" in lower or "off" in lower)

    @staticmethod
    def extract_discount_text(text: str) -> str | None:
        match = re.search(r"((?:R\$\s*)?\d+(?:,\d{2})?\s*(?:%|OFF|off))", text)
        return match.group(1).strip() if match else None

    @staticmethod
    def extract_code(text: str) -> str | None:
        match = re.search(r"(?:c[oó]digo|cupom)\s*[:\-]?\s*([A-Z0-9]{4,20})", text, re.I)
        return match.group(1).upper() if match else None

    @staticmethod
    def extract_min_purchase(text: str) -> Decimal | None:
        match = re.search(r"(?:acima|mínim[ao]|minim[ao]).{0,30}R\$\s*([\d\.]+)(?:,(\d{2}))?", text, re.I)
        if not match:
            return None
        value = match.group(1).replace(".", "")
        cents = match.group(2)
        return to_decimal(f"{value}.{cents}" if cents else value)

    @staticmethod
    def _coupon_from_dict(item: dict) -> Coupon:
        return Coupon(
            store=item.get("store", "Mercado Livre"),
            title=item.get("title", "Cupom Mercado Livre"),
            description=item.get("description", ""),
            url=item.get("url", MercadoLivreCouponService.coupon_url),
            code=item.get("code"),
            discount_text=item.get("discount_text"),
            min_purchase=to_decimal(item.get("min_purchase")),
            category=item.get("category"),
            keywords=item.get("keywords", []),
        )

    @staticmethod
    def save_debug_html(html: str) -> None:
        path = Path("data/debug/mercado_livre_coupons_last.html")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
