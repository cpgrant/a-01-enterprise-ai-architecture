# ADR-003 — Local Model Inference with Ollama and LiteLLM

**Status:** Proposed  
**Project:** AI-A01 — Enterprise AI Reference Architecture

## Context

The architecture must support local inference and avoid coupling agents directly to a particular model provider.

## Decision

Use Ollama for local inference and LiteLLM as a model gateway.

## Consequences

Enables model replacement and local experimentation. Adds a gateway component and requires model-performance testing.

## Alternatives Considered

Direct Ollama API; vLLM; hosted model APIs.

## Validation

Validate the decision during the A01 prototype and
revisit it if operational evidence contradicts the assumptions.
