from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    observations: int
    last_observation_date: str
    is_stale: bool

class ForecastPoint(BaseModel):
    date: str
    predicted_price: float

class ModelForecastComparison(BaseModel):
    model: str
    forecast: list[ForecastPoint] = []
    error: str | None = None

class ForecastResponse(BaseModel):
    model: str
    horizon_months: int
    last_observation_date: str
    last_observed_price: float
    data_age_days: int
    is_stale: bool
    forecast: list[ForecastPoint]
    forecast_comparison: list[ModelForecastComparison] = []
    limitations: list[str]

class HistoryPoint(BaseModel):
    date: str
    avg_monthly_price: float
