from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import settings
from shopping_assistant.collectors import build_default_collectors
from shopping_assistant.db.repositories import PriceRepository
from shopping_assistant.models import AlertRule, AlertRuleType, TrackedProduct
from shopping_assistant.services.comparison import PriceComparisonEngine
from shopping_assistant.services.history import PriceHistoryTracker


router = APIRouter()
templates = Jinja2Templates(directory="shopping_assistant/dashboard/templates")
repository = PriceRepository(settings.database_path)


def _decimal_or_none(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Invalid decimal value") from exc


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    tracked = repository.list_tracked_products()
    snapshots = repository.latest_snapshots(limit=30)
    alerts = repository.list_alert_events(limit=10)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tracked": tracked,
            "snapshots": snapshots,
            "alerts": alerts,
        },
    )


@router.post("/tracked")
async def add_tracked_product(
    query: str = Form(...),
    category: str = Form(""),
    target_price: str = Form(""),
):
    product = TrackedProduct(
        query=query.strip(),
        category=category.strip() or None,
        target_price=_decimal_or_none(target_price.strip()),
    )
    if not product.query:
        raise HTTPException(status_code=400, detail="Query is required")
    repository.add_tracked_product(product)
    return RedirectResponse("/", status_code=303)


@router.post("/alerts")
async def add_alert_rule(
    tracked_product_id: int = Form(...),
    rule_type: str = Form(...),
    threshold: str = Form(""),
):
    repository.add_alert_rule(
        AlertRule(
            tracked_product_id=tracked_product_id,
            rule_type=AlertRuleType(rule_type),
            threshold=_decimal_or_none(threshold.strip()),
        )
    )
    return RedirectResponse("/alerts", status_code=303)


@router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    return templates.TemplateResponse(
        request,
        "alerts.html",
        {
            "tracked": repository.list_tracked_products(),
            "rules": repository.list_alert_rules(active_only=False),
            "events": repository.list_alert_events(limit=50),
            "rule_types": [rule.value for rule in AlertRuleType],
        },
    )


@router.get("/product/{tracked_product_id}", response_class=HTMLResponse)
async def product_page(request: Request, tracked_product_id: int):
    products = {
        product.id: product for product in repository.list_tracked_products()
    }
    product = products.get(tracked_product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Tracked product not found")
    history = repository.history_for_tracked_product(tracked_product_id)
    return templates.TemplateResponse(
        request,
        "product.html",
        {"product": product, "history": history},
    )


@router.get("/api/product/{tracked_product_id}/history")
async def product_history(tracked_product_id: int):
    history = repository.history_for_tracked_product(tracked_product_id)
    return {
        "labels": [snapshot.collected_at.isoformat() for snapshot in history],
        "prices": [float(snapshot.current_price) for snapshot in history],
        "stores": [snapshot.store for snapshot in history],
        "titles": [snapshot.title for snapshot in history],
    }


@router.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...), category: str = Form("")):
    engine = PriceComparisonEngine(build_default_collectors(settings))
    result = await engine.search_all(query.strip(), category=category.strip() or None)
    PriceHistoryTracker(repository).save_snapshots(result.ranked_offers)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tracked": repository.list_tracked_products(),
            "snapshots": repository.latest_snapshots(limit=30),
            "alerts": repository.list_alert_events(limit=10),
            "search_result": result,
        },
    )
