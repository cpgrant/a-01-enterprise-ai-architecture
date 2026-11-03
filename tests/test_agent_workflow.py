
from unittest.mock import MagicMock, patch

import pytest

from agent.workflow import (
    authorize,
    retrieve_orders,
    retrieve_policies,
    analyze,
    validate,
    build_graph,
)


SAMPLE_ORDERS = [
    {
        "order_id": 1001,
        "customer_name": "Nordic Manufacturing",
        "priority": "critical",
        "delay_days": 5,
    }
]

SAMPLE_POLICIES = [
    {
        "document_id": 1,
        "title": "Supplier Delay Policy",
        "content": "Delays over two days must be escalated.",
    }
]


def test_authorize_nonempty_request():
    result = authorize({"request": "Review delayed orders"})
    assert result["authorized"] is True


def test_authorize_empty_request():
    with pytest.raises(PermissionError):
        authorize({"request": ""})


@patch("agent.workflow.httpx.Client")
def test_retrieve_orders(mock_client):
    response = MagicMock()
    response.json.return_value = SAMPLE_ORDERS

    mock_client.return_value.__enter__.return_value.get.return_value = response

    result = retrieve_orders({"authorized": True})

    assert result["orders"] == SAMPLE_ORDERS


def test_retrieve_orders_unauthorized():
    with pytest.raises(PermissionError):
        retrieve_orders({"authorized": False})


@patch("agent.workflow.httpx.Client")
def test_retrieve_policies(mock_client):
    response = MagicMock()
    response.json.return_value = SAMPLE_POLICIES

    mock_client.return_value.__enter__.return_value.get.return_value = response

    result = retrieve_policies({"authorized": True})

    assert result["policies"] == SAMPLE_POLICIES


def test_retrieve_policies_unauthorized():
    with pytest.raises(PermissionError):
        retrieve_policies({"authorized": False})


@patch("agent.workflow.completion")
def test_analyze(mock_completion):
    mock_completion.return_value.choices = [
        MagicMock(
            message=MagicMock(
                content="Escalate order 1001 under Supplier Delay Policy."
            )
        )
    ]

    state = {
        "request": "Review delayed orders",
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }

    result = analyze(state)

    assert "1001" in result["recommendation"]
    mock_completion.assert_called_once()


def test_validate_nonempty_recommendation():
    result = validate({"recommendation": "Escalate order 1001"})
    assert result["validated"] is True


def test_validate_empty_recommendation():
    result = validate({"recommendation": ""})
    assert result["validated"] is False


@patch("agent.workflow.completion")
@patch("agent.workflow.httpx.Client")
def test_complete_workflow(mock_client, mock_completion):
    def fake_get(url):
        response = MagicMock()
        response.raise_for_status.return_value = None

        if url.endswith("/orders/at-risk"):
            response.json.return_value = SAMPLE_ORDERS
        elif url.endswith("/knowledge"):
            response.json.return_value = SAMPLE_POLICIES
        else:
            raise AssertionError(f"Unexpected URL: {url}")

        return response

    mock_client.return_value.__enter__.return_value.get.side_effect = fake_get

    mock_completion.return_value.choices = [
        MagicMock(
            message=MagicMock(
                content="Escalate order 1001 under Supplier Delay Policy."
            )
        )
    ]

    workflow = build_graph()
    result = workflow.invoke({"request": "Review delayed orders"})

    assert result["authorized"] is True
    assert result["orders"] == SAMPLE_ORDERS
    assert result["policies"] == SAMPLE_POLICIES
    assert result["validated"] is True
