# ADR-004 — PostgreSQL and pgvector for Knowledge and State

**Status:** Proposed  
**Project:** AI-A01 — Enterprise AI Reference Architecture

## Context

The prototype requires persistent enterprise data, retrieval and potentially vector similarity search.

## Decision

Use PostgreSQL with pgvector for structured data and embeddings. Keep session state logically separate from knowledge records.

## Consequences

Simplifies the initial deployment while supporting relational queries and vector search. Dedicated vector stores remain an option.

## Alternatives Considered

Qdrant; Neo4j; dedicated vector database.

## Validation

Validate the decision during the A01 prototype and
revisit it if operational evidence contradicts the assumptions.
