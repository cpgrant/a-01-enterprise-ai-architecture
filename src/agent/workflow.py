
import json
import os
from typing import TypedDict

import httpx
from langgraph.graph import StateGraph, START, END
from litellm import completion


API_URL = os.getenv("ENTERPRISE_API_URL", "http://127.0.0.1:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("AI_MODEL", "qwen3.8:27b")


class AgentState(TypedDict, total=False):
    request: str
    authorized: bool
    orders: list[dict]
    policies: list[dict]
    recommendation: str
    validated: bool


def authorize(state: AgentState):
    # Prototype-only authorization.
    # Replace with authenticated identity and policy enforcement.
    permitted = bool(state["request"].strip())
    if not permitted:
        raise PermissionError("Request not authorized")
    return {"authorized": permitted}


def retrieve_orders(state: AgentState):
    if not state.get("authorized"):
        raise PermissionError("Enterprise data access denied")

    with httpx.Client(timeout=30) as client:
        response = client.get(f"{API_URL}/orders/at-risk")
        response.raise_for_status()
        return {"orders": response.json()}


def retrieve_policies(state: AgentState):
    if not state.get("authorized"):
        raise PermissionError("Knowledge access denied")

    with httpx.Client(timeout=30) as client:
        response = client.get(f"{API_URL}/knowledge")
        response.raise_for_status()
        return {"policies": response.json()}


def analyze(state: AgentState):
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
                    "Use only supplied evidence. "
                    "Identify delayed orders, prioritize critical customers, "
                    "and recommend corrective actions. "
                    "Cite order IDs and relevant policy titles. "
                    "Do not claim to have executed any business action."
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

    return {"recommendation": response.choices[0].message.content or ""}


def validate(state: AgentState):
    recommendation = state.get("recommendation", "")
    is_valid = bool(recommendation.strip())

    return {"validated": is_valid}


def build_graph():
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
    workflow = build_graph()

    result = workflow.invoke({
        "request": (
            "Review customer orders at risk of delay and recommend "
            "corrective actions based on enterprise policies."
        )
    })

    print("\n=== AI-A01 ENTERPRISE OPERATIONS ASSISTANT ===")
    print(result["recommendation"])
    print("\nValidated:", result["validated"])
