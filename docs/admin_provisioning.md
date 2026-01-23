# Admin Provisioning (Manual)

Use this checklist to provision plans and subscriptions for a pilot without Stripe.

## Plan Limits

Insert or update plan limits in the database. Example (Postgres):

```sql
INSERT INTO plan_limit (plan_code, max_offers_per_month, created_at)
VALUES ('buyer-pro', 100, NOW());
```

Example (SQLite):

```sql
INSERT INTO plan_limit (plan_code, max_offers_per_month, created_at)
VALUES ('buyer-pro', 100, CURRENT_TIMESTAMP);
```

## Subscriptions

Attach a plan to a vendor (or buyer when buyer billing is enabled):

```sql
INSERT INTO subscription (vendor_id, plan_code, status, started_at)
VALUES (1, 'buyer-pro', 'active', NOW());
```

## Verify in Dashboard

- Open `/dashboard/offers` with a vendor API key.
- Confirm the Plan usage card shows the plan code and current usage.
- If you do not see usage, verify `UsageEvent` rows exist for the vendor.
