from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import tempfile
from app.forecasting import load_monthly_series, build_naive_forecast, evaluate_and_select_model, _active_model, MODEL_PATH, DataValidationError
from app.schemas import HealthResponse, ForecastResponse, HistoryPoint

app = FastAPI(
    title="Way2Agribusiness Price Forecast API",
    version="0.1.0",
    description="Prototype monthly price forecasting API. Forecasts are decision support only.",
)

# Explicitly allow the production frontend, local development, and optional origins
# configured in Render via CORS_ORIGINS (comma-separated). Preview deployments on
# Vercel are supported by the anchored regex without allowing arbitrary domains.
_default_origins = [
    "https://way2agri-price-forecasting.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_extra_origins = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_default_origins + _extra_origins)),
    allow_origin_regex=r"https://[a-zA-Z0-9-]+(?:-[a-zA-Z0-9-]+)*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def get_series():
    try:
        return load_monthly_series()
    except DataValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/health")
def health() -> dict:
    try:
        series = load_monthly_series()
        forecast_meta = build_naive_forecast(series, 1)
        return {
            "status": "ok",
            "observations": int(len(series)),
            "last_observation_date": forecast_meta["last_observation_date"],
            "is_stale": forecast_meta["is_stale"],
        }
    except DataValidationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/history", response_model=list[HistoryPoint])
def history(limit: int = Query(default=24, ge=1, le=249)):
    series = get_series().tail(limit)
    return [
        {"date": date.strftime("%Y-%m-%d"), "avg_monthly_price": round(float(value), 2)}
        for date, value in series.items()
    ]

@app.get("/forecast", response_model=ForecastResponse)
def forecast(horizon: int = Query(default=12, ge=1, le=36)):
    try:
        result = build_naive_forecast(get_series(), horizon)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/model-info")
def model_info():
    return {
        "selected_model": _active_model(),
        "selection_context": "The active model is chosen by POST /train-evaluate using chronological rolling-origin validation and mean MAE. A successful data upload resets the selection to the naive baseline until evaluation is run again.",
        "candidate_models": ["Naive baseline", "Drift", "Holt damped trend", "Holt-Winters additive"],
        "parameters": {
            "selection_metric": "Mean MAE across chronological validation windows",
            "validation_horizon_months": 12,
            "forecast_horizon": "1 to 36 months",
        },
        "warning": (
            "This is a transparent prototype baseline, not a production-approved model. "
            "Revalidate with recent data and business-specific acceptance thresholds."
        ),
    }


@app.post("/dataset")
async def upload_dataset(request: Request):
    """Validate and replace the active monthly CSV dataset using a text/csv request body."""
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"text/csv", "application/csv", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Upload the file as text/csv.")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="The uploaded CSV is empty.")
    if len(body) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV exceeds the 2 MB upload limit.")

    data_path = Path(__file__).resolve().parents[1] / "data" / "price_data.csv"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", dir=data_path.parent, delete=False) as temp:
            temp.write(body)
            temp_path = Path(temp.name)
        series = load_monthly_series(temp_path)
        # Replace only after validation succeeds, so invalid uploads do not destroy active data.
        os.replace(temp_path, data_path)
        # A new dataset invalidates the previous selection; return to baseline until re-evaluated.
        MODEL_PATH.unlink(missing_ok=True)
        last_date = series.index.max().strftime("%Y-%m-%d")
        return {
            "status": "uploaded",
            "observations": int(len(series)),
            "first_observation_date": series.index.min().strftime("%Y-%m-%d"),
            "last_observation_date": last_date,
            "message": "CSV validated and active dataset updated. Forecasts now use the uploaded data.",
        }
    except DataValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.post("/train-evaluate")
def train_evaluate(windows: int = Query(default=4, ge=2, le=8), horizon: int = Query(default=12, ge=3, le=18)):
    """Run rolling-origin model evaluation and persist the best candidate by mean MAE."""
    try:
        return evaluate_and_select_model(get_series(), windows=windows, horizon=horizon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
