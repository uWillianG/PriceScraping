from __future__ import annotations

from config import Settings

from .amazon import AmazonCollector
from .casas_bahia import CasasBahiaCollector
from .google_shopping import GoogleShoppingCollector
from .magalu import MagaluCollector
from .mercado_livre import MercadoLivreCollector
from .shopee import ShopeeCollector


def build_default_collectors(settings: Settings):
    # Temporarily keep only Mercado Livre enabled. The other stores are still
    # implemented below, but their public pages currently serve anti-bot blocks
    # unless official API/affiliate endpoints are configured.
    return [
        MercadoLivreCollector(settings),
        GoogleShoppingCollector(settings),
        # AmazonCollector(settings),
        # MagaluCollector(settings),
        # CasasBahiaCollector(settings),
        # ShopeeCollector(settings),
    ]


__all__ = [
    "AmazonCollector",
    "CasasBahiaCollector",
    "GoogleShoppingCollector",
    "MagaluCollector",
    "MercadoLivreCollector",
    "ShopeeCollector",
    "build_default_collectors",
]
