# ADR-006 — OpenTelemetry for Observability

**Status:** Proposed  
**Project:** AI-A01 — Enterprise AI Reference Architecture

## Context

Agent workflows require traceable execution, performance diagnostics and error visibility.

## Decision

Use OpenTelemetry instrumentation for request, workflow, model and tool spans, with sensitive data redacted.

## Consequences

Provides interoperable tracing but requires instrumentation and an appropriate exporter or backend.

## Alternatives Considered

Application logging only; framework-specific tracing.

## Validation

Validate the decision during the A01 prototype and
revisit it if operational evidence contradicts the assumptions.
