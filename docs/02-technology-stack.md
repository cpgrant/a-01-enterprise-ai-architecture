
# AI-A01 — Technology Stack

## 1. Objective

Define an open-source-first technology stack for the
Enterprise AI Reference Architecture.

The prototype runs locally on Ubuntu/WSL2 with an RTX 4090.

## 2. Selected Stack

| Component | Technology | Responsibility |
|---|---|---|
| API | FastAPI | User requests and API |
| Agent | Python | Business Operations Assistant |
| Orchestration | LangGraph | Workflow execution |
| Model Gateway | LiteLLM | Model abstraction |
| Inference | Ollama | Local language model |
| Knowledge | PostgreSQL + pgvector | Retrieval and state |
| Integration | FastAPI | Synthetic ERP API |
| Governance | Python policy checks | Authorization |
| Observability | OpenTelemetry | Execution tracing |
| Deployment | Docker Compose | Local services |

## 3. Architecture Principles

- Open-source-first
- Vendor-neutral interfaces
- API-first integration
- Modular components
- Local-first development
- Security and governance by design
- Observable and auditable execution
- Human approval for consequential actions

## 4. Minimal Prototype

The Enterprise Operations Assistant will:

1. Receive a business request.
2. Start a LangGraph workflow.
3. Retrieve relevant business knowledge.
4. Query synthetic enterprise data through an API.
5. Check authorization before tool execution.
6. Invoke an Ollama model through LiteLLM.
7. Generate a recommendation with supporting evidence.
8. Record execution traces.

## 5. Technology Boundaries

Each component has a defined responsibility.

Agent Application:
- Business-specific logic

Orchestration:
- Workflow state, sequencing and execution

Model Gateway:
- Model routing and API abstraction

Knowledge:
- Retrieval, embeddings and persistent state

Integration:
- Controlled enterprise system access

Governance:
- Authorization and approval decisions

Observability:
- Traces, errors and execution metrics

## 6. Future Extensions

A02: Multi-agent orchestration and A2A
A03: Advanced RAG and knowledge graphs
A04: MCP and enterprise connectivity
A05: OPA, identity and advanced governance
A06: Digital Business Twin
A07: AgentOps and evaluation
A08: Kubernetes and platform operations

## 7. Selection Criteria

Technologies are evaluated against:

- Open-source availability
- Functional suitability
- Integration simplicity
- Local execution support
- Maintainability
- Observability
- Security
- Enterprise scalability
- Learning value
- Implementation time

## 8. Scope Constraint

A01 is a three-day architecture project.

The reference architecture may describe technologies
not implemented in the prototype.

The prototype should validate the principal architecture
boundaries without becoming a production platform.
