from intentbid.app.core.scoring import score_offer
from intentbid.app.db.models import Offer, RFO


def _base_rfo():
    return RFO(
        category="sneakers",
        constraints={"budget_max": 100, "delivery_deadline_days": 3},
        preferences={"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    )


def _base_offer():
    return Offer(
        rfo_id=1,
        vendor_id=1,
        price_amount=90,
        currency="USD",
        delivery_eta_days=2,
        warranty_months=12,
        return_days=30,
        stock=True,
        metadata_={},
    )


def test_score_over_budget_is_zero():
    rfo = _base_rfo()
    offer = _base_offer()
    offer.price_amount = 150

    score, explain = score_offer(offer, rfo)

    assert score == 0
    assert "over_budget" in explain["penalties"]


def test_score_out_of_stock_is_zero():
    rfo = _base_rfo()
    offer = _base_offer()
    offer.stock = False

    score, explain = score_offer(offer, rfo)

    assert score == 0
    assert "out_of_stock" in explain["penalties"]


def test_score_late_delivery_is_zero():
    rfo = _base_rfo()
    offer = _base_offer()
    offer.delivery_eta_days = 10

    score, explain = score_offer(offer, rfo)

    assert score == 0
    assert "late_delivery" in explain["penalties"]
