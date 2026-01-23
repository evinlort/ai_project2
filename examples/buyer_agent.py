from intentbid.sdk import IntentBidClient


def main() -> None:
    client = IntentBidClient(base_url="http://localhost:8000")

    buyer = client.register_buyer("Pilot Buyer")
    buyer_key = buyer["api_key"]

    rfq = client.create_hardware_rfq(
        category="GPU",
        line_items=[
            {"mpn": "H100-SXM5-80GB", "quantity": 2, "required_specs": {"vram_gb": 80}},
        ],
        constraints={
            "budget_max": 200000,
            "currency": "USD",
            "delivery_deadline_days": 7,
            "region": "US",
            "traceability_required": True,
        },
        compliance={"export_control_ack": True},
        scoring_profile="balanced",
        title="H100 SXM5 urgent",
        summary="Need 2x H100 SXM5 80GB within a week.",
        buyer_api_key=buyer_key,
    )

    rfo_id = rfq["rfo_id"]
    ranking = client.get_ranking_explain(rfo_id, buyer_api_key=buyer_key)

    print("RFQ created:", rfq)
    print("Ranking explain:", ranking)


if __name__ == "__main__":
    main()
