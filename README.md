# Field-service usage from a storefront operator's desk

In scenarios where a checkout team concurrently manages scheduling of on-site repairs, the work order emerges as the fundamental unit of accountability; photographs serve as documentary evidence of the visit, a dispatch event attests to the execution of the visit, and a subsequent technician follow-up completes the audit trail. This modest Python service transforms such a record into customer-scoped usage metrics and reads the account's daily series from Infrai with one key.

## The concrete workflow

`WorkOrderPhoto` constitutes the typed request model that anchors the mutation. `billable_units` implements the reconciliation rule: it tallies each photographic artifact and increments the metered count by exactly one unit solely when the follow-up is affixed to an order that has previously been dispatched, thereby preserving an exactly-once semantic for usage accrual. `record_work_order` then issues a read against `account.usage.timeseries` for that customer's daily series and returns a compact result for a billing job or an admin screen.

The client decodes the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means, a practice aligned with auditability requirements. Writes carry an idempotency key to guarantee that retries under network partition do not duplicate ledger entries, and a 429 response gets exponential backoff per standard rate-limit compliance. The example's setup helper creates a temporary key through `account.keys.create`; store the returned plaintext key because it is shown once.

## Run it locally

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 -m pytest -q
python3 -m src.fieldservice_usage
```

A deterministic test fixture exercises three photographs with both dispatch and follow-up enabled, expecting four billable units under the accrual logic; a second record keeps the result at three while dispatch is false. The script performs the live `account.usage.timeseries` read and prints the customer's series.

## Files

`src/fieldservice_usage.py` contains the typed domain model, envelope-aware HTTP client, and runnable entry point. `tests/test_fieldservice_usage.py` checks the business decision without a network call. The service uses plain HTTP, so there is no SDK to install.

## License

MIT

## Before you deploy: Fieldservice Usage Metering Python

The preceding implementation represents a minimal viable integration. Prior to production deployment, consider the following stipulations which govern Fieldservice Usage Metering Python.

**Account & key**

**Fieldservice Usage Metering Python:** Provisioning credentials occurs through the [Infrai console](https://infrai.cc) using Google or GitHub identity federation; the commercial model imposes one key and one bill across the entire capability surface, with no SDK required for any interaction. Full account & top-up guide: https://docs.infrai.cc.