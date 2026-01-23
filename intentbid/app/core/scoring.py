from typing import Any, Dict

from intentbid.app.db.models import Offer, RFO


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_offer(offer: Offer, rfo: RFO) -> tuple[float, Dict[str, Any]]:
    constraints = rfo.constraints or {}
    preferences = rfo.preferences or {}
    weights = rfo.weights or preferences
    penalties = []

    budget_max = rfo.budget_max if rfo.budget_max is not None else constraints.get("budget_max")
    deadline = (
        rfo.delivery_deadline_days
        if rfo.delivery_deadline_days is not None
        else constraints.get("delivery_deadline_days")
    )

    requested_qty = rfo.quantity
    if requested_qty is None:
        line_items = rfo.line_items or []
        requested_qty = sum(int(item.get("quantity", 0)) for item in line_items) or None

    unit_price = offer.unit_price if offer.unit_price is not None else offer.price_amount
    lead_time_days = (
        offer.lead_time_days if offer.lead_time_days is not None else offer.delivery_eta_days
    )
    available_qty = offer.available_qty
    traceability = offer.traceability or {}

    if budget_max is not None and unit_price is not None and unit_price > budget_max:
        penalties.append("over_budget")
    if available_qty is not None and available_qty <= 0:
        penalties.append("out_of_stock")
    if offer.stock is False:
        penalties.append("out_of_stock")
    if deadline is not None and lead_time_days is not None and lead_time_days > deadline:
        penalties.append("late_delivery")
    if (
        requested_qty is not None
        and available_qty is not None
        and available_qty < requested_qty
    ):
        penalties.append("insufficient_qty")
    if constraints.get("traceability_required") is True:
        required_fields = ("authorized_channel", "invoices_available", "serials_available")
        if any(field not in traceability or traceability[field] is None for field in required_fields):
            penalties.append("traceability_missing")

    price_score = 0.0
    if budget_max:
        price_score = _clamp01(1 - (unit_price / budget_max))

    lead_time_score = 0.0
    if deadline and lead_time_days is not None:
        lead_time_score = _clamp01(1 - (lead_time_days / deadline))

    warranty_score = _clamp01(offer.warranty_months / 24)
    required_fields = ("authorized_channel", "invoices_available", "serials_available")
    has_traceability = all(
        field in traceability and traceability[field] is not None for field in required_fields
    )
    if constraints.get("traceability_required") is True:
        traceability_score = 1.0 if has_traceability else 0.0
    else:
        traceability_score = 1.0 if has_traceability else 0.0

    vendor_reputation_score = 0.0

    profile = (rfo.scoring_profile or "").lower()
    if not weights and profile in {"fastest", "cheapest", "balanced"}:
        profile_weights = {
            "fastest": {
                "w_price": 0.3,
                "w_delivery": 0.5,
                "w_warranty": 0.1,
                "w_traceability": 0.1,
            },
            "cheapest": {
                "w_price": 0.6,
                "w_delivery": 0.2,
                "w_warranty": 0.1,
                "w_traceability": 0.1,
            },
            "balanced": {
                "w_price": 0.4,
                "w_delivery": 0.3,
                "w_warranty": 0.2,
                "w_traceability": 0.1,
            },
        }
        weights = profile_weights.get(profile, {})

    w_price = float(weights.get("w_price", 0.5))
    w_delivery = float(weights.get("w_delivery", 0.3))
    w_warranty = float(weights.get("w_warranty", 0.2))
    w_traceability = float(weights.get("w_traceability", 0.0))
    w_vendor = float(weights.get("w_vendor_reputation", 0.0))

    score = (
        (w_price * price_score)
        + (w_delivery * lead_time_score)
        + (w_warranty * warranty_score)
        + (w_traceability * traceability_score)
        + (w_vendor * vendor_reputation_score)
    )
    if penalties:
        score = 0

    explain = {
        "price_score": price_score,
        "lead_time_score": lead_time_score,
        "warranty_score": warranty_score,
        "traceability_score": traceability_score,
        "vendor_reputation_score": vendor_reputation_score,
        "components": {
            "price_score": price_score,
            "lead_time_score": lead_time_score,
            "warranty_score": warranty_score,
            "traceability_score": traceability_score,
            "vendor_reputation_score": vendor_reputation_score,
        },
        "weights": {
            "w_price": w_price,
            "w_delivery": w_delivery,
            "w_warranty": w_warranty,
            "w_traceability": w_traceability,
            "w_vendor_reputation": w_vendor,
        },
        "penalties": penalties,
    }
    explain["delivery_score"] = lead_time_score
    explain["components"]["delivery_score"] = lead_time_score
    return score, explain
