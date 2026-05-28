from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import Settings
from shopping_assistant.collectors import build_default_collectors
from shopping_assistant.db.repositories import PriceRepository
from shopping_assistant.models import AlertRule, AlertRuleType
from shopping_assistant.services.alerts import DealAlertEngine
from shopping_assistant.services.comparison import PriceComparisonEngine
from shopping_assistant.services.emailer import EmailNotifier
from shopping_assistant.services.history import PriceHistoryTracker


logger = logging.getLogger(__name__)


class PriceCheckScheduler:
    def __init__(self, settings: Settings, repository: PriceRepository) -> None:
        self.settings = settings
        self.repository = repository
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        self.scheduler.add_job(
            self.run_once,
            "interval",
            minutes=self.settings.check_interval_minutes,
            id="price-check",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

    def run_once(self) -> None:
        asyncio.run(self._run_once_async())

    async def _run_once_async(self) -> None:
        tracked_products = self.repository.list_tracked_products(active_only=True)
        collectors = build_default_collectors(self.settings)
        comparison = PriceComparisonEngine(collectors)
        history = PriceHistoryTracker(self.repository)
        alert_engine = DealAlertEngine()
        notifier = EmailNotifier(self.settings)

        all_offers = []
        all_alerts = []
        for product in tracked_products:
            result = await comparison.search_all(product.query, category=product.category)
            all_offers.extend(result.ranked_offers)
            history.save_snapshots(result.ranked_offers, tracked_product_id=product.id)

            rules = self.repository.list_alert_rules(product.id)
            if product.target_price is not None:
                rules.append(
                    AlertRule(
                        rule_type=AlertRuleType.TARGET_PRICE,
                        threshold=product.target_price,
                        tracked_product_id=product.id,
                    )
                )

            lows = {
                alert_engine.offer_key(offer): self.repository.historical_low(offer)
                for offer in result.ranked_offers
            }
            alerts = alert_engine.evaluate(result.ranked_offers, rules, lows)
            for alert in alerts:
                self.repository.record_alert_event(
                    alert_rule_id=None,
                    tracked_product_id=product.id,
                    offer=alert.offer,
                    message=alert.message,
                )
            all_alerts.extend(alerts)

        if all_alerts:
            try:
                notifier.send_deals(all_offers[:20], alerts=all_alerts)
            except Exception as exc:
                logger.warning("Could not send alert email: %s", exc)
