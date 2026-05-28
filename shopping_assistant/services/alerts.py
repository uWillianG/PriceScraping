from __future__ import annotations

from decimal import Decimal

from shopping_assistant.models import AlertRule, AlertRuleType, DealAlert, ProductOffer


class DealAlertEngine:
    def evaluate(
        self,
        offers: list[ProductOffer],
        rules: list[AlertRule],
        historical_lows: dict[str, Decimal | None] | None = None,
    ) -> list[DealAlert]:
        alerts: list[DealAlert] = []
        lows = historical_lows or {}
        for offer in offers:
            offer_key = self.offer_key(offer)
            for rule in rules:
                alert = self._evaluate_rule(offer, rule, lows.get(offer_key))
                if alert:
                    alerts.append(alert)
        return alerts

    @staticmethod
    def offer_key(offer: ProductOffer) -> str:
        return f"{offer.store}|{offer.product_id or offer.url}"

    def _evaluate_rule(
        self,
        offer: ProductOffer,
        rule: AlertRule,
        historical_low: Decimal | None,
    ) -> DealAlert | None:
        if not rule.active:
            return None

        if (
            rule.rule_type == AlertRuleType.TARGET_PRICE
            and rule.threshold is not None
            and offer.current_price <= rule.threshold
        ):
            return DealAlert(
                rule_type=rule.rule_type,
                offer=offer,
                threshold=rule.threshold,
                message=f"{offer.title} is at or below target price R$ {rule.threshold}.",
            )

        if (
            rule.rule_type == AlertRuleType.DISCOUNT_PERCENT
            and rule.threshold is not None
            and offer.discount_percent is not None
            and offer.discount_percent >= rule.threshold
        ):
            return DealAlert(
                rule_type=rule.rule_type,
                offer=offer,
                threshold=rule.threshold,
                message=f"{offer.title} has {offer.discount_percent}% discount.",
            )

        if (
            rule.rule_type == AlertRuleType.HISTORICAL_LOW
            and historical_low is not None
            and offer.current_price <= historical_low
        ):
            return DealAlert(
                rule_type=rule.rule_type,
                offer=offer,
                historical_price=historical_low,
                message=f"{offer.title} reached a historical low at R$ {offer.current_price}.",
            )

        return None
