from typing import Any, Dict

from intentbid.app.db.models import Offer, RFO


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_offer(offer: Offer, rfo: RFO) -> tuple[float, Dict[str, Any]]:
    constraints = rfo.constraints or {}
    preferences = rfo.preferences or {}
    penalties = []

    budget_max = constraints.get("budget_max")
    deadline = constraints.get("delivery_deadline_days")

    if budget_max is not None and offer.price_amount > budget_max:
        penalties.append("over_budget")
    if offer.stock is False:
        penalties.append("out_of_stock")
    if deadline is not None and offer.delivery_eta_days > deadline:
        penalties.append("late_delivery")

    if penalties:
        return 0, {"penalties": penalties}

    price_score = 0.0
    if budget_max:
        price_score = _clamp01(1 - (offer.price_amount / budget_max))

    delivery_score = 0.0
    if deadline:
        delivery_score = _clamp01(1 - (offer.delivery_eta_days / deadline))

    warranty_score = _clamp01(offer.warranty_months / 24)

    w_price = float(preferences.get("w_price", 0.5))
    w_delivery = float(preferences.get("w_delivery", 0.3))
    w_warranty = float(preferences.get("w_warranty", 0.2))

    score = (w_price * price_score) + (w_delivery * delivery_score) + (w_warranty * warranty_score)

    explain = {
        "price_score": price_score,
        "delivery_score": delivery_score,
        "warranty_score": warranty_score,
        "weights": {
            "w_price": w_price,
            "w_delivery": w_delivery,
            "w_warranty": w_warranty,
        },
        "penalties": penalties,
    }
    return score, explain
