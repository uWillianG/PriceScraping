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

CATEGORIES = [
    {
        "slug": "appliances",
        "name": "Eletrodomésticos",
        "description": "Geladeira, fogão, micro-ondas, lava e seca e climatização.",
        "examples": ["geladeira frost free", "micro-ondas midea", "lava e seca"],
        "products": [
            {"name": "Geladeira", "query": "geladeira frost free"},
            {"name": "Micro-ondas", "query": "micro-ondas"},
            {"name": "Fogão", "query": "fogão 4 bocas"},
            {"name": "Lava e seca", "query": "lava e seca"},
            {"name": "Ar-condicionado", "query": "ar condicionado split"},
            {"name": "Air fryer", "query": "air fryer"},
        ],
    },
    {
        "slug": "furniture",
        "name": "Móveis",
        "description": "Sofás, mesas, cadeiras, camas, armários e estantes.",
        "examples": ["sofa retratil", "mesa de jantar", "guarda roupa casal"],
        "products": [
            {"name": "Sofá", "query": "sofa retratil"},
            {"name": "Mesa de jantar", "query": "mesa de jantar"},
            {"name": "Guarda-roupa", "query": "guarda roupa casal"},
            {"name": "Cama", "query": "cama box casal"},
            {"name": "Rack", "query": "rack para tv"},
            {"name": "Cadeira", "query": "cadeira escritorio"},
        ],
    },
    {
        "slug": "electronics",
        "name": "Eletrônicos",
        "description": "TVs, caixas de som, automação residencial e acessórios.",
        "examples": ["smart tv 55", "soundbar", "camera wifi"],
        "products": [
            {"name": "Smart TV", "query": "smart tv 55"},
            {"name": "Soundbar", "query": "soundbar"},
            {"name": "Câmera Wi-Fi", "query": "camera wifi"},
            {"name": "Alexa/Echo", "query": "echo dot alexa"},
            {"name": "Roteador", "query": "roteador wifi"},
            {"name": "Projetor", "query": "projetor"},
        ],
    },
    {
        "slug": "home_decor",
        "name": "Decoração",
        "description": "Luminárias, tapetes, quadros, cortinas e organização.",
        "examples": ["tapete sala", "luminaria pendente", "cortina blackout"],
        "products": [
            {"name": "Tapete", "query": "tapete sala"},
            {"name": "Luminária", "query": "luminaria pendente"},
            {"name": "Cortina", "query": "cortina blackout"},
            {"name": "Quadros", "query": "quadros decorativos"},
            {"name": "Espelho", "query": "espelho decorativo"},
            {"name": "Organizadores", "query": "organizador casa"},
        ],
    },
]

CATEGORY_BY_SLUG = {category["slug"]: category for category in CATEGORIES}


def _decimal_or_none(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Invalid decimal value") from exc


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"categories": CATEGORIES},
    )


@router.get("/category/{category_slug}", response_class=HTMLResponse)
async def category_page(request: Request, category_slug: str):
    category = CATEGORY_BY_SLUG.get(category_slug)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse(
        request,
        "select_product.html",
        {"category": category},
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


@router.get("/tracked", response_class=HTMLResponse)
async def tracked_page(request: Request):
    return templates.TemplateResponse(
        request,
        "tracked.html",
        {
            "tracked": repository.list_tracked_products(),
            "snapshots": repository.latest_snapshots(limit=30),
            "alerts": repository.list_alert_events(limit=10),
        },
    )


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


@router.post("/results", response_class=HTMLResponse)
async def results(request: Request, query: str = Form(...), category: str = Form(...)):
    category_config = CATEGORY_BY_SLUG.get(category)
    if category_config is None:
        raise HTTPException(status_code=404, detail="Category not found")

    engine = PriceComparisonEngine(build_default_collectors(settings))
    result = await engine.search_all(query.strip(), category=category)
    PriceHistoryTracker(repository).save_snapshots(result.ranked_offers)
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "category": category_config,
            "search_result": result,
        },
    )


@router.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...), category: str = Form("")):
    selected_category = category.strip() or "appliances"
    return await results(request, query=query, category=selected_category)
