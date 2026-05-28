from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _decimal(name: str, default: str) -> Decimal:
    return Decimal(os.getenv(name, default))


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Home Shopping Price Assistant")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/price_history.db"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    min_request_delay_seconds: float = float(os.getenv("MIN_REQUEST_DELAY_SECONDS", "1.0"))
    max_request_delay_seconds: float = float(os.getenv("MAX_REQUEST_DELAY_SECONDS", "3.0"))
    check_interval_minutes: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
    user_agent: str = os.getenv(
        "USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    )

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    smtp_to_email: str = os.getenv("SMTP_TO_EMAIL", "")
    smtp_use_tls: bool = _bool("SMTP_USE_TLS", True)

    default_discount_threshold_percent: Decimal = _decimal(
        "DEFAULT_DISCOUNT_THRESHOLD_PERCENT", "20"
    )
    fake_discount_original_price_inflation_percent: Decimal = _decimal(
        "DEFAULT_FAKE_DISCOUNT_ORIGINAL_PRICE_INFLATION_PERCENT", "15"
    )

    amazon_access_key: str = os.getenv("AMAZON_ACCESS_KEY", "")
    amazon_secret_key: str = os.getenv("AMAZON_SECRET_KEY", "")
    amazon_partner_tag: str = os.getenv("AMAZON_PARTNER_TAG", "")
    amazon_marketplace: str = os.getenv("AMAZON_MARKETPLACE", "www.amazon.com.br")

    shopee_partner_id: str = os.getenv("SHOPEE_PARTNER_ID", "")
    shopee_secret_key: str = os.getenv("SHOPEE_SECRET_KEY", "")
    shopee_affiliate_endpoint: str = os.getenv("SHOPEE_AFFILIATE_ENDPOINT", "")

    magalu_search_endpoint: str = os.getenv("MAGALU_SEARCH_ENDPOINT", "")
    magalu_api_token: str = os.getenv("MAGALU_API_TOKEN", "")

    casas_bahia_search_endpoint: str = os.getenv("CASAS_BAHIA_SEARCH_ENDPOINT", "")
    casas_bahia_api_token: str = os.getenv("CASAS_BAHIA_API_TOKEN", "")


settings = Settings()
