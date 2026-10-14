# Architecture

```text
Next.js dashboard ──GET /forecast, /history──> FastAPI forecast service
                                                  │
                                                  └── validated monthly CSV
Django admin/workflow ──GET /api/forecast-proxy──> FastAPI
```

FastAPI owns prediction endpoints and input validation. Django is an optional admin/workflow
layer and proxies requests to FastAPI. Next.js calls FastAPI directly for the demo. In a
production system, route browser requests through a secured backend or gateway as appropriate.

## Operational controls
- Data validation on load; missing months and duplicate monthly rows fail explicitly.
- Health endpoint reports observation count and data freshness.
- Forecast response reports stale-data status and limitations.
- Production additions: authentication/authorization, rate limiting, secrets, HTTPS, structured
  logs, monitoring, persistent metrics, CI tests, and scheduled model evaluation.
