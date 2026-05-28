from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from contextlib import closing
from pathlib import Path
import sqlite3

from shopping_assistant.db.database import get_connection, initialize_database
from shopping_assistant.models import (
    AlertRule,
    AlertRuleType,
    PriceSnapshot,
    ProductOffer,
    TrackedProduct,
    to_decimal,
)


def _dt(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _money(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


class PriceRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        initialize_database(self.database_path)

    def add_tracked_product(self, product: TrackedProduct) -> int:
        with closing(get_connection(self.database_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tracked_products (query, category, target_price, active, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    product.query,
                    product.category,
                    _money(product.target_price),
                    int(product.active),
                    product.created_at.isoformat(),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_tracked_products(self, active_only: bool = False) -> list[TrackedProduct]:
        query = "SELECT * FROM tracked_products"
        params: tuple[int, ...] = ()
        if active_only:
            query += " WHERE active = ?"
            params = (1,)
        query += " ORDER BY created_at DESC"
        with closing(get_connection(self.database_path)) as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._tracked_from_row(row) for row in rows]

    def add_alert_rule(self, rule: AlertRule) -> int:
        with closing(get_connection(self.database_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO alert_rules (tracked_product_id, rule_type, threshold, active)
                VALUES (?, ?, ?, ?)
                """,
                (
                    rule.tracked_product_id,
                    rule.rule_type.value,
                    _money(rule.threshold),
                    int(rule.active),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_alert_rules(
        self, tracked_product_id: int | None = None, active_only: bool = True
    ) -> list[AlertRule]:
        clauses = []
        params: list[object] = []
        if tracked_product_id is not None:
            clauses.append("tracked_product_id = ?")
            params.append(tracked_product_id)
        if active_only:
            clauses.append("active = 1")
        sql = "SELECT * FROM alert_rules"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC"
        with closing(get_connection(self.database_path)) as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._alert_rule_from_row(row) for row in rows]

    def save_offer(
        self, offer: ProductOffer, tracked_product_id: int | None = None
    ) -> int:
        with closing(get_connection(self.database_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO price_snapshots (
                    tracked_product_id, product_id, store, title, category,
                    current_price, original_price, discount_percent, url,
                    image_url, collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tracked_product_id,
                    offer.product_id,
                    offer.store,
                    offer.title,
                    offer.category,
                    str(offer.current_price),
                    _money(offer.original_price),
                    _money(offer.discount_percent),
                    offer.url,
                    offer.image_url,
                    offer.collected_at.isoformat(),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def latest_snapshots(self, limit: int = 50) -> list[PriceSnapshot]:
        with closing(get_connection(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT * FROM price_snapshots ORDER BY collected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._snapshot_from_row(row) for row in rows]

    def history_for_offer(self, offer: ProductOffer, limit: int = 100) -> list[PriceSnapshot]:
        with closing(get_connection(self.database_path)) as connection:
            rows = connection.execute(
                """
                SELECT * FROM price_snapshots
                WHERE store = ?
                  AND (product_id = ? OR url = ?)
                ORDER BY collected_at DESC
                LIMIT ?
                """,
                (offer.store, offer.product_id, offer.url, limit),
            ).fetchall()
        return [self._snapshot_from_row(row) for row in rows]

    def history_for_tracked_product(
        self, tracked_product_id: int, limit: int = 250
    ) -> list[PriceSnapshot]:
        with closing(get_connection(self.database_path)) as connection:
            rows = connection.execute(
                """
                SELECT * FROM price_snapshots
                WHERE tracked_product_id = ?
                ORDER BY collected_at ASC
                LIMIT ?
                """,
                (tracked_product_id, limit),
            ).fetchall()
        return [self._snapshot_from_row(row) for row in rows]

    def historical_low(self, offer: ProductOffer) -> Decimal | None:
        history = self.history_for_offer(offer)
        prices = [snapshot.current_price for snapshot in history]
        return min(prices) if prices else None

    def record_alert_event(
        self,
        *,
        alert_rule_id: int | None,
        tracked_product_id: int | None,
        offer: ProductOffer,
        message: str,
    ) -> int:
        with closing(get_connection(self.database_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO alert_events (
                    alert_rule_id, tracked_product_id, store, title,
                    current_price, url, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_rule_id,
                    tracked_product_id,
                    offer.store,
                    offer.title,
                    str(offer.current_price),
                    offer.url,
                    message,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_alert_events(self, limit: int = 50) -> list[sqlite3.Row]:
        with closing(get_connection(self.database_path)) as connection:
            return list(
                connection.execute(
                    "SELECT * FROM alert_events ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            )

    def _tracked_from_row(self, row: sqlite3.Row) -> TrackedProduct:
        return TrackedProduct(
            id=row["id"],
            query=row["query"],
            category=row["category"],
            target_price=to_decimal(row["target_price"]),
            active=bool(row["active"]),
            created_at=_dt(row["created_at"]),
        )

    def _alert_rule_from_row(self, row: sqlite3.Row) -> AlertRule:
        return AlertRule(
            id=row["id"],
            tracked_product_id=row["tracked_product_id"],
            rule_type=AlertRuleType(row["rule_type"]),
            threshold=to_decimal(row["threshold"]),
            active=bool(row["active"]),
        )

    def _snapshot_from_row(self, row: sqlite3.Row) -> PriceSnapshot:
        return PriceSnapshot(
            id=row["id"],
            tracked_product_id=row["tracked_product_id"],
            product_id=row["product_id"],
            store=row["store"],
            title=row["title"],
            category=row["category"],
            current_price=to_decimal(row["current_price"]) or Decimal("0.00"),
            original_price=to_decimal(row["original_price"]),
            discount_percent=to_decimal(row["discount_percent"]),
            url=row["url"],
            image_url=row["image_url"],
            collected_at=_dt(row["collected_at"]),
        )
