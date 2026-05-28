from __future__ import annotations

import argparse
import asyncio

from config import settings
from shopping_assistant.collectors import build_default_collectors
from shopping_assistant.db.database import initialize_database
from shopping_assistant.logging_config import configure_logging
from shopping_assistant.services.comparison import PriceComparisonEngine


async def search_once(query: str, category: str | None) -> None:
    collectors = build_default_collectors(settings)
    engine = PriceComparisonEngine(collectors)
    result = await engine.search_all(query, category=category)
    for offer in result.ranked_offers:
        discount = f" ({offer.discount_percent}% off)" if offer.discount_percent else ""
        print(f"{offer.store}: R$ {offer.current_price} - {offer.title}{discount}")
        print(f"  {offer.url}")


def main() -> None:
    configure_logging()
    initialize_database(settings.database_path)

    parser = argparse.ArgumentParser(description=settings.app_name)
    parser.add_argument("query", nargs="?", help="Product search query")
    parser.add_argument("--category", help="Optional category label")
    args = parser.parse_args()

    if args.query:
        asyncio.run(search_once(args.query, args.category))
    else:
        print("Database initialized. Run: python main.py \"geladeira frost free\"")


if __name__ == "__main__":
    main()
