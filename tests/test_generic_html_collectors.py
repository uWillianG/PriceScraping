from config import settings
from shopping_assistant.collectors.amazon import AmazonCollector
from shopping_assistant.collectors.casas_bahia import CasasBahiaCollector
from shopping_assistant.collectors.magalu import MagaluCollector
from shopping_assistant.collectors.shopee import ShopeeCollector


def test_magalu_extracts_offer_from_html():
    html = """
    <div data-testid="product-card">
      <a href="/geladeira-brastemp/p/123456/ed/refr/">Geladeira Brastemp</a>
      <span>R$ 2.199,90</span>
    </div>
    """
    offers = MagaluCollector(settings).extract_offers(html, "appliances")
    assert len(offers) == 1
    assert offers[0].store == "Magazine Luiza"
    assert str(offers[0].current_price) == "2199.90"


def test_casas_bahia_extracts_offer_from_html():
    html = """
    <article>
      <a href="/geladeira-electrolux/p/98765">Geladeira Electrolux</a>
      <span>R$ 2.499,00</span>
    </article>
    """
    offers = CasasBahiaCollector(settings).extract_offers(html, "appliances")
    assert len(offers) == 1
    assert offers[0].store == "Casas Bahia"


def test_amazon_extracts_offer_from_html():
    html = """
    <div data-component-type="s-search-result">
      <h2><a href="/dp/B00TESTE">Aspirador de Po</a></h2>
      <span>R$ 399,90</span>
    </div>
    """
    offers = AmazonCollector(settings).extract_offers(html, "appliances")
    assert len(offers) == 1
    assert offers[0].store == "Amazon Brasil"


def test_shopee_extracts_offer_from_html():
    html = """
    <div data-sqe="item">
      <a href="/Produto-Teste-i.123.456">Luminaria Decorativa</a>
      <span>R$ 89,99</span>
    </div>
    """
    offers = ShopeeCollector(settings).extract_offers(html, "home decor")
    assert len(offers) == 1
    assert offers[0].store == "Shopee Brasil"
