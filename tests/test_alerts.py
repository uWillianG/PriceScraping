from decimal import Decimal

from shopping_assistant.models import AlertRule, AlertRuleType, ProductOffer
from shopping_assistant.services.alerts import DealAlertEngine


def test_target_price_alert_triggers():
    offer = ProductOffer("Store", "Geladeira", Decimal("2500"), None, None, "https://x.test")
    rule = AlertRule(AlertRuleType.TARGET_PRICE, threshold=Decimal("2600"))

    alerts = DealAlertEngine().evaluate([offer], [rule])

    assert len(alerts) == 1
    assert alerts[0].rule_type == AlertRuleType.TARGET_PRICE


def test_discount_alert_triggers():
    offer = ProductOffer(
        "Store",
        "Cooktop",
        Decimal("700"),
        Decimal("1000"),
        None,
        "https://x.test",
    )
    rule = AlertRule(AlertRuleType.DISCOUNT_PERCENT, threshold=Decimal("25"))

    alerts = DealAlertEngine().evaluate([offer], [rule])

    assert len(alerts) == 1


def test_historical_low_alert_triggers():
    offer = ProductOffer("Store", "Sofa", Decimal("799"), None, None, "https://x.test")
    key = DealAlertEngine.offer_key(offer)
    rule = AlertRule(AlertRuleType.HISTORICAL_LOW)

    alerts = DealAlertEngine().evaluate([offer], [rule], {key: Decimal("800")})

    assert len(alerts) == 1
