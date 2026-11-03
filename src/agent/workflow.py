import json
import os
from typing import TypedDict

import httpx
from langgraph.graph import StateGraph, START, END
from litellm import completion

from agent.policy import Principal, authorize_action, AuthorizationError
from agent.validation import validate_recommendation
from observability.tracing import configure_tracing, get_tracer, traced_node


API_URL = os.getenv("ENTERPRISE_API_URL", "http://127.0.0.1:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("AI_MODEL", "qwen3.8:27b")


class AgentState(TypedDict, total=False):
    request: str
    user_id: str
    role: str
    authorized: bool
    orders: list[dict]
    policies: list[dict]
    recommendation: str
    validated: bool


def get_principal(state: AgentState) -> Principal:
    """Construct the principal from supplied workflow identity fields."""
    return Principal(
        user_id=state.get("user_id", ""),
        role=state.get("role", ""),
    )

@traced_node("authorize")
def authorize(state: AgentState):
    """Check request validity and required read permissions."""

    request = state.get("request", "")

    if not request.strip():
        raise AuthorizationError("Empty business request")

    principal = get_principal(state)

    authorize_action(principal, "orders:read")
    authorize_action(principal, "policies:read")

    return {"authorized": True}

@traced_node("retrieve_orders")
def retrieve_orders(state: AgentState):
    """Retrieve delayed orders only when access is permitted."""

    if not state.get("authorized"):
        raise PermissionError("Enterprise data access denied")

    principal = get_principal(state)
    authorize_action(principal, "orders:read")

    with httpx.Client(timeout=30) as client:
        response = client.get(f"{API_URL}/orders/at-risk")
        response.raise_for_status()

        return {"orders": response.json()}

@traced_node("retrieve_policies")
def retrieve_policies(state: AgentState):
    """Retrieve enterprise policies only when access is permitted."""

    if not state.get("authorized"):
        raise PermissionError("Knowledge access denied")

    principal = get_principal(state)
    authorize_action(principal, "policies:read")

    with httpx.Client(timeout=30) as client:
        response = client.get(f"{API_URL}/knowledge")
        response.raise_for_status()

        return {"policies": response.json()}


@traced_node("analyze")
def analyze(state: AgentState):
    """Generate structured recommendations from enterprise evidence."""

    if not state.get("authorized"):
        raise PermissionError("Agent analysis denied")

    evidence = {
        "orders": state["orders"],
        "policies": state["policies"],
    }

    response = completion(
        model=f"ollama/{MODEL}",
        api_base=OLLAMA_URL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise operations analyst. "
                    "Use only the supplied orders and policies. "
                    "Recommend corrective actions for delayed orders. "
                    "Prioritize critical customers. "
                    "Return ONLY valid JSON with this structure: "
                    '{"recommendations": ['
                    '{"order_id": 1001, '
                    '"action": "Escalate supplier delay", '
                    '"reason": "Critical customer with a five-day delay", '
                    '"policy_ids": [1]}'
                    "]}. "
                    "The example values are illustrative; use only IDs "
                    "and facts present in the supplied evidence. "
                    "Each recommendation must have a unique order_id. "
                    "Cite actual policy document_id values. "
                    "Do not invent order IDs, policy IDs, currencies, "
                    "monetary amounts or business outcomes. "
                    "Do not include markdown formatting or commentary. "
                    "Do not claim to have executed any action."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Business request: {state['request']}\n\n"
                    f"Evidence:\n{json.dumps(evidence, indent=2)}"
                ),
            },
        ],
    )

    return {
        "recommendation": response.choices[0].message.content or ""
    }


@traced_node("validate")
def validate(state: AgentState):
    """Validate model JSON and its references to enterprise records."""

    report = validate_recommendation(
        output=state.get("recommendation", ""),
        orders=state["orders"],
        policies=state["policies"],
    )

    return {
        "validated": True,
        "recommendation": report.model_dump_json(indent=2),
    }




def build_graph():
    """Build the enterprise operations LangGraph workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("authorize", authorize)
    graph.add_node("retrieve_orders", retrieve_orders)
    graph.add_node("retrieve_policies", retrieve_policies)
    graph.add_node("analyze", analyze)
    graph.add_node("validate", validate)

    graph.add_edge(START, "authorize")
    graph.add_edge("authorize", "retrieve_orders")
    graph.add_edge("retrieve_orders", "retrieve_policies")
    graph.add_edge("retrieve_policies", "analyze")
    graph.add_edge("analyze", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


if __name__ == "__main__":
    configure_tracing()
    tracer = get_tracer()

    workflow = build_graph()

    with tracer.start_as_current_span("ai-a01.workflow") as span:
        span.set_attribute("workflow.name", "enterprise-operations")
        span.set_attribute("workflow.mode", "read-only")

        result = workflow.invoke({
            "user_id": "demo-analyst",
            "role": "analyst",
            "request": (
                "Review customer orders at risk of delay and recommend "
                "corrective actions based on enterprise policies."
            ),
        })

        span.set_attribute(
            "workflow.validated",
            result["validated"],
        )

        print("\n=== AI-A01 ENTERPRISE OPERATIONS ASSISTANT ===")
        print("\nUser:", result["user_id"])
        print("Role:", result["role"])
        print("Authorized:", result["authorized"])

        print("\n=== RECOMMENDATION ===")
        print(result["recommendation"])
        print("\nValidated:", result["validated"])