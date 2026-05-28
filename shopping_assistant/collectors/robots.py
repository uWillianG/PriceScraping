from __future__ import annotations

import asyncio
from functools import lru_cache
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


@lru_cache(maxsize=128)
def _parser_for_base(base_url: str) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(f"{base_url}/robots.txt")
    return parser


async def can_fetch(url: str, user_agent: str, timeout_seconds: int = 10) -> bool:
    try:
        import aiohttp
    except ImportError:
        return True

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    parser = _parser_for_base(base_url)

    if not parser.entries and parser.default_entry is None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/robots.txt",
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds),
                ) as response:
                    if response.status >= 400:
                        return True
                    parser.parse((await response.text()).splitlines())
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return True

    return parser.can_fetch(user_agent, url)
