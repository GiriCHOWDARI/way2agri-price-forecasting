# Dataset refresh workflow

The dashboard includes an **Upload CSV** control that sends the CSV text to `POST /dataset`.
The API accepts `text/csv`, limits uploads to 2 MB, validates the required `date` and
`avg_monthly_price` columns, positive numeric prices, one observation per calendar month,
continuous monthly coverage, and at least 24 monthly observations. Invalid uploads return
HTTP 422 and leave the active dataset unchanged. A valid upload replaces the local active
CSV and the dashboard refreshes its history and forecast.

Example request:

```powershell
$csv = Get-Content .\price_data.csv -Raw
Invoke-RestMethod -Uri http://127.0.0.1:8000/dataset -Method Post -ContentType 'text/csv' -Body $csv
```

## Important deployment note

This prototype stores the active dataset in a local CSV file. That is suitable for local
experimentation, but not for multi-instance or ephemeral production deployments. For
production, store versioned datasets in durable object storage or a database, restrict uploads
to authenticated/authorized users, keep an audit trail, and make dataset updates atomic across
all app instances. Do not upload data unless its commodity, market, unit, source, and reporting
period are understood and consistent.

The current forecast engine remains a naive baseline: each future month repeats the latest
observed price. Uploading fresh data resolves the stale-data issue, but does not itself make the
forecast model accurate or production-approved.
