from __future__ import annotations

from shopping_assistant.collectors.base import BaseCollector, CollectorNotConfigured
from shopping_assistant.models import ProductOffer


class AmazonCollector(BaseCollector):
    store_name = "Amazon Brasil"

    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        if not (
            self.settings.amazon_access_key
            and self.settings.amazon_secret_key
            and self.settings.amazon_partner_tag
        ):
            self.logger.info("Amazon PA-API credentials are not configured")
            return []

        raise CollectorNotConfigured(
            "Amazon PA-API signing is credential-specific; configure an approved "
            "PA-API client before enabling live Amazon searches."
        )
