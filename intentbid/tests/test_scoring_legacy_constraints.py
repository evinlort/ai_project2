from intentbid.app.core.scoring import score_offer
from intentbid.app.db.models import Offer, RFO


def test_scoring_uses_legacy_constraints_when_columns_missing():
    rfo = RFO(
        category="sneakers",
        constraints={"budget_max": 120, "delivery_deadline_days": 4},
        preferences={"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        budget_max=None,
        delivery_deadline_days=None,
    )
    offer = Offer(
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

    score, explain = score_offer(offer, rfo)

    assert score > 0
    assert explain["penalties"] == []
