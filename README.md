# Way2Agribusiness Monthly Price Forecasting — Prototype

A starter project for the assignment: FastAPI forecast API, a small Next.js dashboard,
and an optional Django admin/workflow scaffold. This is a **prototype**, not a production
price recommendation system.

## Important data limitation
The supplied data contains `date` and `avg_monthly_price` only and ends in September 2025.
It does not identify the commodity, market, unit, or price definition. The API therefore
reports the dataset's last observation and marks forecasts as stale when data is old.
Update `backend/data/price_data.csv` with verified, current data before using the forecast
for decisions. Do not combine different commodities, markets, units, or price definitions.

## Project structure
- `backend/`: FastAPI API, forecast logic, tests and dataset
- `frontend/`: Next.js demo dashboard
- `django_admin/`: optional Django scaffold for admin/business workflow
- `docs/`: architecture and deployment notes

## 1. Run FastAPI (Windows PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` for interactive API docs.
Health: `http://127.0.0.1:8000/health`
Forecast: `http://127.0.0.1:8000/forecast?horizon=12`

## 2. Run the Next.js frontend
Install Node.js 20+ first. In a second terminal:
```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```
Open `http://localhost:3000`. `NEXT_PUBLIC_API_BASE_URL` defaults to `http://127.0.0.1:8000`.
If the browser blocks requests, verify FastAPI is running and the frontend origin is in the API CORS allowlist.

## 3. Optional Django scaffold
```powershell
cd django_admin
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
```
Django admin is at `http://127.0.0.1:8001/admin/`. This scaffold is for administration/workflows.
FastAPI remains the forecast service. Do not duplicate training logic in Django.

## API endpoints
- `GET /health`: API and data freshness metadata
- `GET /history?limit=24`: most recent observations
- `GET /forecast?horizon=12`: forecast from the active selected model and metadata
- `POST /train-evaluate?windows=4&horizon=12`: rolling-origin evaluation; selects by mean MAE and saves the active model choice
- `GET /model-info`: model approach and known limitations

Initially, the forecast uses a naive baseline. Run model evaluation after refreshing data to compare the naive, drift, Holt damped trend, and Holt-Winters additive candidates with chronological rolling-origin validation. The selected model name is persisted in `backend/data/active_model.json`; the forecast endpoint refits that model on the active series. This is still a prototype, not a production-approved forecasting service. The included source dataset is stale relative to the current date, so the API marks forecasts as stale and does not pretend to have live prices.

See `docs/model-training.md` for model selection details and guardrails.

## Testing
```powershell
cd backend
python -m pip install -r requirements.txt
pytest -q
```

## Before deployment
1. Verify commodity, market, price unit and source metadata.
2. Replace the sample CSV with a verified current series and maintain a data refresh timestamp.
3. Re-run chronological / rolling-origin validation after each dataset update.
4. Set an agreed business error threshold and compare against the naive baseline.
5. Add authentication, rate limits, structured logs, secret management and persistent monitoring.
6. Use HTTPS and configure CORS for only the deployed frontend origin.
7. Keep human approval for procurement decisions. Forecasts are decision support only.

## Data schema
CSV must have exactly these required columns:
- `date`: parseable date; monthly series is normalized to month start
- `avg_monthly_price`: positive numeric price

If multiple commodities or markets are added, add explicit identifiers and filter to one series
before forecasting. Do not aggregate unrelated series silently.

## Deployment environment variables

- **Render backend (optional):** `CORS_ORIGINS` may contain additional comma-separated frontend origins. The production Vercel origin and localhost development origins are already allowed. Vercel preview URLs are allowed by a restricted `*.vercel.app` origin pattern.
- **Vercel frontend:** set `NEXT_PUBLIC_API_BASE_URL` to `https://way2agri-price-forecasting-1.onrender.com` in Project Settings → Environment Variables, then redeploy. The frontend uses this production API URL as its default if the variable is absent.

After deploying the backend, verify `/health` and test CSV upload from the deployed frontend. A successful local test suite cannot guarantee that hosting settings or the deployed environment variables are correct.
