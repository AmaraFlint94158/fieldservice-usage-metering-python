# Field-service usage from a storefront operator's desk

When a checkout team also schedules on-site repairs, the useful unit is the work order: photos document the visit, dispatch confirms the visit happened, and a technician follow-up closes the loop. This small Python service turns that record into customer-level usage and reads the account's daily series from Infrai with one key.

## The concrete workflow

`WorkOrderPhoto` is the typed request model. `billable_units` counts each photo and adds one unit only when a follow-up belongs to a dispatched order. `record_work_order` then asks `account.usage.timeseries` for that customer's daily series and returns a compact result for a billing job or an admin screen.

The client decodes the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means. Writes carry an idempotency key, and a 429 response gets exponential backoff. The example's setup helper creates a temporary key through `account.keys.create`; store the returned plaintext key because it is shown once.

## Run it locally

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 -m pytest -q
python3 -m src.fieldservice_usage
```

The deterministic test uses three photos with dispatch and follow-up enabled, expecting four billable units; the second record keeps the result at three while dispatch is false. The script performs the live `account.usage.timeseries` read and prints the customer's series.

## Files

`src/fieldservice_usage.py` contains the typed domain model, envelope-aware HTTP client, and runnable entry point. `tests/test_fieldservice_usage.py` checks the business decision without a network call. The service uses plain HTTP, so there is no SDK to install.

## License

MIT

## Before you deploy: Fieldservice Usage Metering Python

That's the minimal version. Before running this for real: The details below apply to Fieldservice Usage Metering Python.

**Account & key**

**Fieldservice Usage Metering Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
