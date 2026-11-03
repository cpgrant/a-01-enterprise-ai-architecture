
import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from agent.policy import AuthorizationError, Principal, authorize_action
from agent.validation import validate_recommendation
from agent.workflow import (
    authorize,
    retrieve_orders,
    retrieve_policies,
    analyze,
    validate,
    build_graph,
)


# ------------------------------------------------------------
# Test data
# ------------------------------------------------------------

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

VALID_REPORT = {
    "recommendations": [
        {
            "order_id": 1001,
            "action": "Escalate supplier delay",
            "reason": "Critical customer with a five-day delay",
            "policy_ids": [1],
        }
    ]
}

VALID_JSON = json.dumps(VALID_REPORT)


def valid_state():
    return {
        "request": "Review delayed orders",
        "user_id": "demo-analyst",
        "role": "analyst",
    }


def validation_state(report=VALID_REPORT):
    return {
        "recommendation": json.dumps(report),
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }


# ------------------------------------------------------------
# Authorization tests
# ------------------------------------------------------------

def test_authorize_valid_analyst():
    assert authorize(valid_state())["authorized"] is True


def test_authorize_empty_request():
    state = valid_state()
    state["request"] = ""

    with pytest.raises(AuthorizationError):
        authorize(state)


def test_authorize_missing_identity():
    state = valid_state()
    state["user_id"] = ""

    with pytest.raises(AuthorizationError):
        authorize(state)


def test_authorize_unknown_role():
    state = valid_state()
    state["role"] = "unknown"

    with pytest.raises(AuthorizationError):
        authorize(state)


def test_authorize_missing_role():
    state = valid_state()
    state["role"] = ""

    with pytest.raises(AuthorizationError):
        authorize(state)


def test_policy_allows_read():
    principal = Principal("demo-analyst", "analyst")

    assert authorize_action(principal, "orders:read") is True


def test_policy_denies_write():
    principal = Principal("demo-analyst", "analyst")

    with pytest.raises(AuthorizationError):
        authorize_action(principal, "orders:write")


# ------------------------------------------------------------
# Enterprise data retrieval tests
# ------------------------------------------------------------

@patch("agent.workflow.httpx.Client")
def test_retrieve_orders(mock_client):
    response = MagicMock()
    response.json.return_value = SAMPLE_ORDERS

    mock_client.return_value.__enter__.return_value.get.return_value = response

    state = {**valid_state(), "authorized": True}

    assert retrieve_orders(state)["orders"] == SAMPLE_ORDERS
    response.raise_for_status.assert_called_once()


@patch("agent.workflow.httpx.Client")
def test_retrieve_orders_unauthorized(mock_client):
    state = {**valid_state(), "authorized": False}

    with pytest.raises(PermissionError):
        retrieve_orders(state)

    mock_client.assert_not_called()


@patch("agent.workflow.httpx.Client")
def test_retrieve_orders_unknown_role(mock_client):
    state = {**valid_state(), "authorized": True, "role": "unknown"}

    with pytest.raises(AuthorizationError):
        retrieve_orders(state)

    mock_client.assert_not_called()


@patch("agent.workflow.httpx.Client")
def test_retrieve_policies(mock_client):
    response = MagicMock()
    response.json.return_value = SAMPLE_POLICIES

    mock_client.return_value.__enter__.return_value.get.return_value = response

    state = {**valid_state(), "authorized": True}

    assert retrieve_policies(state)["policies"] == SAMPLE_POLICIES
    response.raise_for_status.assert_called_once()


@patch("agent.workflow.httpx.Client")
def test_retrieve_policies_unauthorized(mock_client):
    state = {**valid_state(), "authorized": False}

    with pytest.raises(PermissionError):
        retrieve_policies(state)

    mock_client.assert_not_called()


@patch("agent.workflow.httpx.Client")
def test_retrieve_policies_unknown_role(mock_client):
    state = {**valid_state(), "authorized": True, "role": "unknown"}

    with pytest.raises(AuthorizationError):
        retrieve_policies(state)

    mock_client.assert_not_called()


# ------------------------------------------------------------
# LLM analysis tests
# ------------------------------------------------------------

@patch("agent.workflow.completion")
def test_analyze(mock_completion):
    mock_completion.return_value.choices = [
        MagicMock(
            message=MagicMock(content=VALID_JSON)
        )
    ]

    state = {
        **valid_state(),
        "authorized": True,
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }

    result = analyze(state)

    assert json.loads(result["recommendation"]) == VALID_REPORT
    mock_completion.assert_called_once()


def test_analyze_unauthorized():
    state = {
        **valid_state(),
        "authorized": False,
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }

    with pytest.raises(PermissionError):
        analyze(state)


# ------------------------------------------------------------
# Structured validation tests
# ------------------------------------------------------------

def test_validate_valid_recommendation():
    result = validate(validation_state())

    assert result["validated"] is True
    assert json.loads(result["recommendation"]) == VALID_REPORT


def test_validate_empty_recommendation():
    state = {
        "recommendation": "",
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }

    with pytest.raises(ValueError):
        validate(state)


def test_validate_unknown_order():
    report = {
        "recommendations": [
            {
                **VALID_REPORT["recommendations"][0],
                "order_id": 9999,
            }
        ]
    }

    with pytest.raises(ValueError, match="Unknown order ID"):
        validate(validation_state(report))


def test_validate_unknown_policy():
    report = {
        "recommendations": [
            {
                **VALID_REPORT["recommendations"][0],
                "policy_ids": [999],
            }
        ]
    }

    with pytest.raises(ValueError, match="Unknown policy ID"):
        validate(validation_state(report))


def test_validate_duplicate_orders():
    item = VALID_REPORT["recommendations"][0]

    report = {
        "recommendations": [item.copy(), item.copy()]
    }

    with pytest.raises(ValidationError, match="Duplicate order"):
        validate(validation_state(report))


def test_validate_malformed_json():
    state = {
        "recommendation": "{invalid json",
        "orders": SAMPLE_ORDERS,
        "policies": SAMPLE_POLICIES,
    }

    with pytest.raises(ValueError, match="not valid JSON"):
        validate(state)


def test_validate_rejects_unsupported_currency():
    report = {
        "recommendations": [
            {
                **VALID_REPORT["recommendations"][0],
                "currency": "USD",
            }
        ]
    }

    with pytest.raises(ValidationError):
        validate(validation_state(report))


def test_validate_rejects_missing_reason():
    item = VALID_REPORT["recommendations"][0].copy()
    del item["reason"]

    report = {"recommendations": [item]}

    with pytest.raises(ValidationError):
        validate(validation_state(report))


def test_validate_rejects_empty_recommendations():
    report = {"recommendations": []}

    with pytest.raises(ValidationError):
        validate(validation_state(report))


def test_validation_function_returns_typed_report():
    report = validate_recommendation(
        output=VALID_JSON,
        orders=SAMPLE_ORDERS,
        policies=SAMPLE_POLICIES,
    )

    assert report.recommendations[0].order_id == 1001


# ------------------------------------------------------------
# Complete LangGraph workflow tests
# ------------------------------------------------------------

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
            message=MagicMock(content=VALID_JSON)
        )
    ]

    result = build_graph().invoke(valid_state())

    assert result["authorized"] is True
    assert result["orders"] == SAMPLE_ORDERS
    assert result["policies"] == SAMPLE_POLICIES
    assert result["validated"] is True

    assert json.loads(result["recommendation"]) == VALID_REPORT

    mock_completion.assert_called_once()


@patch("agent.workflow.httpx.Client")
def test_complete_workflow_rejects_unknown_role(mock_client):
    state = {**valid_state(), "role": "unknown"}

    with pytest.raises(AuthorizationError):
        build_graph().invoke(state)

    mock_client.assert_not_called()
