# ADR-005 — Separate Policy Enforcement from Agent Reasoning

**Status:** Proposed  
**Project:** AI-A01 — Enterprise AI Reference Architecture

## Context

LLM-generated decisions cannot be trusted to authorize access to enterprise systems.

## Decision

Enforce authorization outside the LLM, at the enterprise tool-execution boundary, using deterministic checks. Deny by default.

## Consequences

Protects business systems from unauthorized agent actions. Requires maintained policies, identity context and audit records.

## Alternatives Considered

Prompt-only restrictions; application checks without a dedicated enforcement boundary.

## Validation

Validate the decision during the A01 prototype and
revisit it if operational evidence contradicts the assumptions.
