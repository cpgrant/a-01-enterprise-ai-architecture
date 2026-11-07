# AI-A01 — Operations Runbook

**Project:** Enterprise AI Reference Architecture  
**Status:** Working local prototype  
**Environment:** Windows 11, Ubuntu WSL2, Docker Desktop, Ollama

## 1. Prerequisites

- Windows 11 with Ubuntu WSL2
- Docker Desktop with WSL integration enabled
- Python virtual environment configured in `.venv`
- Ollama installed with `qwen3.8:27b`
- PostgreSQL database initialized through Docker Compose

## 2. Start the application

Open Docker Desktop on Windows and ensure the Docker engine is running.

Open Ubuntu WSL and execute:

```bash
cd ~/development/ai-projects/a-01-enterprise-ai-architecture
source .venv/bin/activate

sudo systemctl start ollama
docker compose -f infra/compose.yaml up -d
```

## 3. Verify services

```bash
docker compose -f infra/compose.yaml ps
curl http://127.0.0.1:8001/health
ollama list
```

Expected API health response:

```json
{"status":"healthy","database":"connected"}
```

## 4. Run the AI agent

```bash
ENTERPRISE_API_URL=http://127.0.0.1:8001 \
PYTHONPATH=src python -m agent.workflow
```

The workflow performs:

1. RBAC authorization.
2. Retrieval of at-risk enterprise orders.
3. Retrieval of enterprise policies.
4. Qwen 3.8 analysis through LiteLLM and Ollama.
5. Pydantic structured-response validation.

It returns JSON recommendations and OpenTelemetry traces.

## 5. Explore the API

With Docker running, open:

http://127.0.0.1:8001/docs

Available endpoints:

| Endpoint | Description |
|---|---|
| `/health` | Application and database health |
| `/orders` | All synthetic orders |
| `/orders/at-risk` | Delayed orders |
| `/knowledge` | Enterprise policy documents |

## 6. Run semantic retrieval

```bash
PYTHONPATH=src python -m knowledge.search
```

This runs an independent semantic retrieval demonstration using EmbeddingGemma and PostgreSQL pgvector.

## 7. Run tests

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

Verified baseline: 39 passing tests.

## 8. Observability

The workflow uses OpenTelemetry with console span export.

To save execution output to a temporary file:

```bash
ENTERPRISE_API_URL=http://127.0.0.1:8001 \
PYTHONPATH=src python -m agent.workflow \
  > /tmp/a01-trace.log 2>&1
```

Inspect node spans:

```bash
grep -E '"name": "(ai-a01.workflow|agent\.)' /tmp/a01-trace.log
```

## 9. Shut down

```bash
docker compose -f infra/compose.yaml down
sudo systemctl stop ollama
deactivate
```

Docker's persistent PostgreSQL volume is retained. Do not use `down -v` unless intentionally deleting the database volume.

## 10. Troubleshooting

**Cannot connect to Docker daemon:** Start Docker Desktop and check Settings → Resources → WSL Integration.

**API health check fails:** Run `docker compose -f infra/compose.yaml ps` and `docker compose -f infra/compose.yaml logs api postgres`.

**Ollama connection fails:** Run `sudo systemctl start ollama` and `ollama list`.

**Python import errors:** Activate `.venv` and run commands with `PYTHONPATH=src`.

**Database login fails:** Check the local `infra/.env` configuration without exposing passwords or committing secrets.

## 11. Security and operational limitations

AI-A01 is a local demonstration environment using synthetic data.

- User identities and roles are caller-supplied, not independently authenticated.
- Direct FastAPI endpoints are not protected by production authentication.
- Model output validation checks schemas and source identifiers but does not guarantee the factual correctness of every claim.
- The main agent does not write to enterprise business systems.
- Semantic retrieval is a standalone demonstration and not yet part of the main LangGraph workflow.

Do not expose the service publicly without additional security controls.