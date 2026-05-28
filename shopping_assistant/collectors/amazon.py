from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import hmac
import json
from typing import Any

from shopping_assistant.collectors.base import CollectorError
from shopping_assistant.collectors.generic_html import GenericHtmlCollector
from shopping_assistant.models import ProductOffer, compute_discount_percent, to_decimal


class AmazonCollector(GenericHtmlCollector):
    store_name = "Amazon Brasil"
    base_url = "https://www.amazon.com.br"
    search_url_template = "https://www.amazon.com.br/s?k={query}"
    search_encoding = "quote_plus"
    card_selector = "div[data-component-type='s-search-result']"
    link_selector = "a.a-link-normal.s-no-outline, h2 a, a[href*='/dp/']"
    wait_selector = "div[data-component-type='s-search-result'], a[href*='/dp/']"
    debug_file = "amazon_last.html"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if (
            self.settings.amazon_access_key
            and self.settings.amazon_secret_key
            and self.settings.amazon_partner_tag
        ):
            return await self._search_paapi(query, category)

        return await super().search(query, category)

    async def _search_paapi(
        self, query: str, category: str | None = None
    ) -> list[ProductOffer]:
        payload = {
            "Keywords": query,
            "PartnerTag": self.settings.amazon_partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.settings.amazon_marketplace,
            "ItemCount": 10,
            "SearchIndex": self.settings.amazon_search_index,
            "Resources": [
                "Images.Primary.Medium",
                "ItemInfo.Title",
                "Offers.Listings.Price",
                "Offers.Listings.SavingBasis",
                "OffersV2.Listings.Price",
            ],
        }
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        url = f"https://{self.settings.amazon_paapi_host}/paapi5/searchitems"
        headers = self._signed_headers(body)
        data = await self.get_json(
            url,
            headers=headers,
            params=None,
            check_robots=False,
            retries=1,
        )
        return self._normalize_paapi_response(data, category)

    def _signed_headers(self, body: str) -> dict[str, str]:
        host = self.settings.amazon_paapi_host
        region = self.settings.amazon_paapi_region
        service = "ProductAdvertisingAPI"
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical_headers = (
            "content-encoding:amz-1.0\n"
            f"host:{host}\n"
            f"x-amz-date:{amz_date}\n"
            f"x-amz-target:{target}\n"
        )
        signed_headers = "content-encoding;host;x-amz-date;x-amz-target"
        canonical_request = "\n".join(
            [
                "POST",
                "/paapi5/searchitems",
                "",
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )
        credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = self._signature_key(
            self.settings.amazon_secret_key, date_stamp, region, service
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.settings.amazon_access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Accept": "application/json",
            "Authorization": authorization,
            "Content-Encoding": "amz-1.0",
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": target,
            "User-Agent": self.settings.user_agent,
            "_body": body,
        }

    async def get_json(self, url, *, params=None, headers=None, retries=2, check_robots=True):
        body = None
        if headers and "_body" in headers:
            headers = dict(headers)
            body = headers.pop("_body")
        if body is None:
            return await super().get_json(
                url,
                params=params,
                headers=headers,
                retries=retries,
                check_robots=check_robots,
            )

        try:
            import aiohttp
        except ImportError as exc:
            from shopping_assistant.collectors.base import CollectorNotConfigured

            raise CollectorNotConfigured("aiohttp is required for Amazon PA-API.") from exc

        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=body.encode("utf-8"), headers=headers) as response:
                if response.status >= 400:
                    text = (await response.text())[:500]
                    raise CollectorError(
                        f"Amazon PA-API returned HTTP {response.status}: {text}"
                    )
                return await response.json()

    @staticmethod
    def _signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
        key_date = hmac.new(
            ("AWS4" + secret_key).encode("utf-8"),
            date_stamp.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        key_region = hmac.new(key_date, region.encode("utf-8"), hashlib.sha256).digest()
        key_service = hmac.new(key_region, service.encode("utf-8"), hashlib.sha256).digest()
        return hmac.new(key_service, b"aws4_request", hashlib.sha256).digest()

    def _normalize_paapi_response(
        self, data: dict[str, Any], category: str | None
    ) -> list[ProductOffer]:
        items = data.get("SearchResult", {}).get("Items", [])
        offers: list[ProductOffer] = []
        for item in items:
            title = (
                item.get("ItemInfo", {})
                .get("Title", {})
                .get("DisplayValue")
            )
            url = item.get("DetailPageURL")
            current = self._extract_current_price(item)
            if not title or not url or current is None:
                continue
            original = self._extract_original_price(item)
            offers.append(
                ProductOffer(
                    store=self.store_name,
                    title=title,
                    current_price=current,
                    original_price=original,
                    discount_percent=compute_discount_percent(current, original),
                    url=url,
                    product_id=item.get("ASIN"),
                    category=category,
                    image_url=(
                        item.get("Images", {})
                        .get("Primary", {})
                        .get("Medium", {})
                        .get("URL")
                    ),
                )
            )
        return offers

    def _extract_current_price(self, item: dict[str, Any]):
        listings = item.get("Offers", {}).get("Listings", [])
        if listings:
            return to_decimal(listings[0].get("Price", {}).get("Amount"))
        v2_listings = item.get("OffersV2", {}).get("Listings", [])
        if v2_listings:
            price = v2_listings[0].get("Price", {})
            return to_decimal(price.get("Money", {}).get("Amount") or price.get("Amount"))
        return None

    def _extract_original_price(self, item: dict[str, Any]):
        listings = item.get("Offers", {}).get("Listings", [])
        if listings:
            return to_decimal(listings[0].get("SavingBasis", {}).get("Amount"))
        return None
