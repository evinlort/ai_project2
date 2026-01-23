from datetime import datetime, timedelta, timezone

from intentbid.sdk import IntentBidClient


def main() -> None:
    vendor_key = "<vendor_key>"
    client = IntentBidClient(base_url="http://localhost:8000", api_key=vendor_key)

    offer = client.submit_hardware_offer(
        rfo_id=1,
        unit_price=95000.0,
        currency="USD",
        available_qty=2,
        lead_time_days=4,
        condition="new",
        warranty_months=12,
        return_days=30,
        traceability={
            "authorized_channel": True,
            "invoices_available": True,
            "serials_available": True,
            "notes": "Authorized distributor batch.",
        },
        valid_until=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        metadata={"source": "vendor_bot"},
    )

    print("Offer submitted:", offer)


if __name__ == "__main__":
    main()
