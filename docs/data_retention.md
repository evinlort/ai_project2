# Data Retention & PII Minimalism

## Data Retention

- Retain RFQs, offers, and audit logs for the minimum period required for compliance.
- Purge expired RFQs and old webhook delivery logs on a scheduled basis.
- Retain only aggregated usage metrics when detailed records are no longer needed.

## PII Minimalism

- Store only business contact details required for transactions.
- Avoid storing payment details in the MVP; rely on external invoicing.
- Redact API keys and secrets in logs (configured in request logging).
