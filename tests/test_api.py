import pytest
from fastapi.testclient import TestClient
from main import app
import database

client = TestClient(app)

def test_add_metrics():
    response = client.post("/metrics/", json={
        "experiment_id": "test_exp",
        "variant_id": "control",
        "date": "2023-01-01",
        "impressions": 1000,
        "successes": 100
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_get_allocations():
    # Add some test data
    test_add_metrics()
    
    response = client.get("/allocations/test_exp?for_date=2023-01-02")
    assert response.status_code == 200
    data = response.json()
    assert "allocations" in data
    assert sum(data["allocations"].values()) == pytest.approx(100, 0.1)