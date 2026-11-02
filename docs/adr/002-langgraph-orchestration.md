# ADR-002 — LangGraph for Agent Orchestration

**Status:** Proposed  
**Project:** AI-A01 — Enterprise AI Reference Architecture

## Context

The prototype needs explicit workflow state, sequencing, branching and controlled tool execution.

## Decision

Use LangGraph for the A01 workflow prototype. Evaluate other orchestration approaches in A02.

## Consequences

Provides explicit execution flow and state management, but introduces framework dependencies.

## Alternatives Considered

Custom Python workflow; CrewAI; AutoGen; Temporal.

## Validation

Validate the decision during the A01 prototype and
revisit it if operational evidence contradicts the assumptions.
