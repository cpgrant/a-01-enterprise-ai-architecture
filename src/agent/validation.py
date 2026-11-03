
"""Structured validation for AI-A01 recommendations."""

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class OrderRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: int
    action: str = Field(min_length=5)
    reason: str = Field(min_length=10)
    policy_ids: list[int] = Field(min_length=1)


class RecommendationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendations: list[OrderRecommendation] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_orders(self):
        ids = [item.order_id for item in self.recommendations]

        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate order recommendations")

        return self


def validate_recommendation(
    output: str,
    orders: list[dict],
    policies: list[dict],
) -> RecommendationReport:
    """Validate JSON structure and source-record references."""

    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("Model output is not valid JSON") from exc

    report = RecommendationReport.model_validate(data)

    known_orders = {int(order["order_id"]) for order in orders}
    known_policies = {
        int(policy["document_id"]) for policy in policies
    }

    for item in report.recommendations:
        if item.order_id not in known_orders:
            raise ValueError(
                f"Unknown order ID: {item.order_id}"
            )

        for policy_id in item.policy_ids:
            if policy_id not in known_policies:
                raise ValueError(
                    f"Unknown policy ID: {policy_id}"
                )

    return report
