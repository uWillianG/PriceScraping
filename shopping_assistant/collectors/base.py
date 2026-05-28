from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Any

from config import Settings
from shopping_assistant.collectors.robots import can_fetch
from shopping_assistant.models import ProductOffer


class CollectorError(Exception):
    """Base error for collector failures."""


class CollectorNotConfigured(CollectorError):
    """Raised when a collector needs credentials or an endpoint not configured yet."""


class CollectorBlocked(CollectorError):
    """Raised when robots.txt, a store, or bot protection blocks collection."""


class BaseCollector(ABC):
    store_name: str

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def search(self, query: str, category: str | None = None) -> list[ProductOffer]:
        raise NotImplementedError

    async def polite_delay(self) -> None:
        await asyncio.sleep(
            random.uniform(
                self.settings.min_request_delay_seconds,
                self.settings.max_request_delay_seconds,
            )
        )

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 2,
        check_robots: bool = True,
    ) -> dict[str, Any]:
        try:
            import aiohttp
        except ImportError as exc:
            raise CollectorNotConfigured(
                "aiohttp is required for live collection. Install requirements.txt first."
            ) from exc

        if check_robots and not await can_fetch(
            url, self.settings.user_agent, self.settings.request_timeout_seconds
        ):
            raise CollectorBlocked(f"robots.txt disallows fetching {url}")

        merged_headers = {"User-Agent": self.settings.user_agent}
        if headers:
            merged_headers.update(headers)

        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout_seconds)
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            await self.polite_delay()
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        url, params=params, headers=merged_headers
                    ) as response:
                        if response.status in {401, 403, 429}:
                            body = (await response.text())[:300]
                            raise CollectorBlocked(
                                f"{self.store_name} returned HTTP {response.status}: {body}"
                            )
                        response.raise_for_status()
                        return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(2**attempt)
                    continue
                break

        raise CollectorError(f"{self.store_name} request failed: {last_error}")

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 2,
        check_robots: bool = True,
    ) -> str:
        try:
            import aiohttp
        except ImportError as exc:
            raise CollectorNotConfigured(
                "aiohttp is required for live collection. Install requirements.txt first."
            ) from exc

        if check_robots and not await can_fetch(
            url, self.settings.user_agent, self.settings.request_timeout_seconds
        ):
            raise CollectorBlocked(f"robots.txt disallows fetching {url}")

        merged_headers = {"User-Agent": self.settings.user_agent}
        if headers:
            merged_headers.update(headers)

        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout_seconds)
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            await self.polite_delay()
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        url, params=params, headers=merged_headers
                    ) as response:
                        if response.status in {401, 403, 429}:
                            body = (await response.text())[:300]
                            raise CollectorBlocked(
                                f"{self.store_name} returned HTTP {response.status}: {body}"
                            )
                        response.raise_for_status()
                        return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(2**attempt)
                    continue
                break

        raise CollectorError(f"{self.store_name} request failed: {last_error}")
