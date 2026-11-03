
import os

import httpx
import pytest


API_URL = os.getenv(
    "ENTERPRISE_API_URL",
    "http://127.0.0.1:8001"
)


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=API_URL, timeout=15) as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_orders(client):
    response = client.get("/orders")
    assert response.status_code == 200

    orders = response.json()
    assert len(orders) == 6


def test_at_risk_orders(client):
    response = client.get("/orders/at-risk")
    assert response.status_code == 200

    orders = response.json()

    assert len(orders) == 4
    assert all(order["delay_days"] > 0 for order in orders)
    assert {o["order_id"] for o in orders} == {
        1001, 1003, 1004, 1006
    }


def test_critical_customers_first(client):
    orders = client.get("/orders/at-risk").json()

    assert orders[0]["priority"] == "critical"
    assert orders[1]["priority"] == "critical"


def test_knowledge(client):
    response = client.get("/knowledge")
    assert response.status_code == 200

    documents = response.json()
    assert len(documents) == 3

    titles = {doc["title"] for doc in documents}
    assert "Supplier Delay Policy" in titles
    assert "Customer Priority Policy" in titles
    assert "Supply Chain Recovery Guidelines" in titles
