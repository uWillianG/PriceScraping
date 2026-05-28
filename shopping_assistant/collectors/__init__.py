from __future__ import annotations

from config import Settings

from .amazon import AmazonCollector
from .casas_bahia import CasasBahiaCollector
from .magalu import MagaluCollector
from .mercado_livre import MercadoLivreCollector
from .shopee import ShopeeCollector


def build_default_collectors(settings: Settings):
    return [
        MercadoLivreCollector(settings),
        AmazonCollector(settings),
        MagaluCollector(settings),
        CasasBahiaCollector(settings),
        ShopeeCollector(settings),
    ]


__all__ = [
    "AmazonCollector",
    "CasasBahiaCollector",
    "MagaluCollector",
    "MercadoLivreCollector",
    "ShopeeCollector",
    "build_default_collectors",
]
