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
