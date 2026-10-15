from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["observations"] >= 24

def test_forecast_default_horizon():
    response = client.get("/forecast")
    assert response.status_code == 200
    body = response.json()
    assert body["horizon_months"] == 12
    assert len(body["forecast"]) == 12
    assert "is_stale" in body

def test_forecast_rejects_invalid_horizon():
    assert client.get("/forecast?horizon=0").status_code == 422
    assert client.get("/forecast?horizon=37").status_code == 422

def test_history():
    response = client.get("/history?limit=6")
    assert response.status_code == 200
    assert len(response.json()) == 6

def test_dataset_upload_rejects_invalid_csv_without_replacing_data():
    before = client.get("/health").json()["last_observation_date"]
    response = client.post(
        "/dataset",
        content="month,price\n2025-01-01,100\n",
        headers={"Content-Type": "text/csv"},
    )
    assert response.status_code == 422
    assert client.get("/health").json()["last_observation_date"] == before


def test_dataset_upload_requires_csv_content_type():
    response = client.post(
        "/dataset",
        content="date,avg_monthly_price\n",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 415


def test_forecast_dates_follow_last_observation_and_staleness_is_reported():
    response = client.get("/forecast?horizon=3")
    assert response.status_code == 200
    body = response.json()
    dates = [point["date"] for point in body["forecast"]]
    assert dates == ["2025-10-01", "2025-11-01", "2025-12-01"]
    assert body["last_observation_date"] == "2025-09-01"
    # The bundled sample data is intentionally old; the API must disclose this.
    assert body["is_stale"] is True


def test_forecast_includes_side_by_side_model_comparison():
    response = client.get("/forecast?horizon=3")
    assert response.status_code == 200
    body = response.json()
    comparison = {item["model"]: item for item in body["forecast_comparison"]}
    assert {"Naive baseline", "Drift", "Holt damped trend", "Holt-Winters additive"} <= set(comparison)
    naive_values = [point["predicted_price"] for point in comparison["Naive baseline"]["forecast"]]
    drift_values = [point["predicted_price"] for point in comparison["Drift"]["forecast"]]
    assert len(naive_values) == 3
    assert len(drift_values) == 3
    assert len(set(naive_values)) == 1
    assert len(set(drift_values)) > 1


def test_cors_allows_production_frontend_for_dataset_post():
    response = client.options(
        "/dataset",
        headers={
            "Origin": "https://way2agri-price-forecasting.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://way2agri-price-forecasting.vercel.app"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_allows_vercel_preview_origin():
    origin = "https://way2agri-price-forecasting-giri-team.vercel.app"
    response = client.options(
        "/dataset",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
