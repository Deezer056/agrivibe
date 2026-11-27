# AgriVibe

**An AI assistant for Sri Lankan paddy farmers.** A farmer asks a question in plain language. AgriVibe answers it from official Department of Agriculture guidance, checks their field's satellite and weather data, and cites where every fact came from. When the guidance doesn't cover a question, it says so instead of guessing.

Built as my capstone for the STEMLink AI Engineer Bootcamp.

---

## The problem

Ask a general chatbot the same fertiliser question three times and you get three different, confident answers. None of them match the published figures. A farmer can't tell a guess from a fact, and a wrong dose costs money and crops.

AgriVibe is built so that doesn't happen. Facts come from real documents, numbers come from real measurements, and the system is tested to refuse rather than invent.

## What it does

- **Answers from documents, with citations.** Cultivation guides, subsidy circulars and field records are indexed in a vector store. Answers quote the passage they used (RAG).
- **Knows the farmer's field.** It pulls Sentinel-2 crop-health (NDVI) and weather data through a separate MCP server I built: [fieldsat-mcp-server](https://github.com/Deezer056/fieldsat-mcp-server).
- **Remembers the conversation.** Follow-up questions work, and each farmer's field is remembered across chats (PostgreSQL).
- **Shows its working.** The chat UI ([agrivibe-frontend](https://github.com/Deezer056/agrivibe-frontend), Gradio) shows which agents ran, what each found, and the cited sources under every answer.
- **Stays safe.** Guardrails block prompt injection, hide phone numbers, stop runaway loops and withhold unsafe fertiliser doses.

## How it works

```
Farmer ──► FastAPI /chat ──► Orchestrator agent (LangGraph)
                                │
          ┌──────────────┬──────┴───────┬──────────────┐
          ▼              ▼              ▼              ▼
   Knowledge agent  Weather agent  Farm-context   Advisory agent
   (RAG: Pinecone    (FieldSat     agent          (writes the
    + reranker)       MCP)         (FieldSat MCP)  final advice)
```

One **orchestrator** talks to the farmer and works out what's needed. It calls four **specialist agents** as tools, then combines their findings into one answer. Only the orchestrator keeps the conversation; each specialist starts fresh on every call.

## Quality and safety

**Retrieval was measured, not assumed.** I tested three search strategies on a question set with known answers (full write-up in [`reports/retrieval_report.md`](reports/retrieval_report.md)):

| Retrieval | Recall@5 | Precision@5 | MRR |
|---|---|---|---|
| Vector search | 0.593 | 0.289 | 0.519 |
| Hybrid (vector + BM25) | 0.370 | 0.200 | 0.467 |
| **Hybrid + cross-encoder rerank** (used) | **0.593** | **0.311** | **0.648** |

Hybrid search on its own made results *worse*. Adding a reranker fixed that and gave the best ranking, so that's what the app uses.

**Guardrails**, mapped to the OWASP LLM Top 10 (2025):

| Risk | Guardrail |
|---|---|
| Prompt injection in chat or in tool output | Input moderation + tool-output fence |
| Personal data (phone numbers) | PII redaction, also masked in traces |
| Agent stuck in a loop, burning tokens | Model- and tool-call limits per turn |
| Unsafe fertiliser advice | Dose-range check that withholds out-of-range doses |

**Evaluation gate in CI.** Every change to the agent runs an eval set scored by an LLM judge. The build fails if the pass rate drops below the baseline, or if any safety case fails even once.

**Observability.** Every request is traced in Langfuse, and guardrail triggers are recorded as scores you can chart in production.

## Tech stack

| Area | Tools |
|---|---|
| API | Python 3.13, FastAPI, Pydantic |
| Agents | LangChain, LangGraph |
| Models | OpenAI (chat + embeddings) |
| Retrieval | Pinecone, BM25, cross-encoder reranker |
| Tools | MCP (FastMCP), Copernicus Sentinel-2, Open-Meteo |
| Memory | PostgreSQL (LangGraph checkpointer + store) |
| Observability | Langfuse |
| Testing | pytest (runs with a fake model, no API keys), LLM-as-judge evals |
| Deployment | Docker, AWS ECS + ALB, Terraform, GitHub Actions (OIDC, no stored keys) |

## Run it locally

You need Python 3.13, [uv](https://docs.astral.sh/uv/), a PostgreSQL database, and the [FieldSat MCP server](https://github.com/Deezer056/fieldsat-mcp-server) running on port 8001.

```bash
uv sync

# Create .env with at least:
#   OPENAI_API_KEY=...
#   PINECONE_API_KEY=...
#   DATABASE_URL=postgresql://...
# Optional: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY for tracing

uv run fastapi dev src/agrivibe/main.py     # http://127.0.0.1:8000/docs
```

Then index the sample documents with `POST /knowledge/index` and start chatting with `POST /chat`.

**Tests and evals**

```bash
uv run pytest -q                  # unit tests, no keys needed
uv run python eval/run_bench.py rerank   # retrieval benchmark
uv run python evals/run_evals.py         # agent evals
```

## API

| Method | Path | What it does |
|---|---|---|
| `POST` | `/chat` | Send a message and get the agent's reply |
| `GET` | `/threads` | List your conversations |
| `GET` / `DELETE` | `/threads/{id}` | Read or delete one conversation |
| `POST` | `/knowledge/index` | Add documents to the knowledge base |
| `POST` | `/knowledge/search` | Search the knowledge base directly |
| `POST` | `/feedback` | Rate an answer (sent to Langfuse) |
| `GET` | `/me` | The current farmer |
| `GET` | `/health` | Health check |

## Project layout

```
src/agrivibe/
  agents/      orchestrator + specialist agents (knowledge, weather, farm context, advisory)
  api/         FastAPI routes
  core/        guardrails, reranker, MCP client, tracing, database
  service/     chat, threads, knowledge
eval/          retrieval benchmark
evals/         agent evals, LLM judge, CI gate
infra/         Terraform for AWS (ECS, ALB, ECR, IAM)
tests/         pytest suite
```

## Credits

Course structure and teaching material are by STEMLink. The agents, retrieval pipeline, guardrails, evaluations and infrastructure in this repository are my own work.

**Dakshina Lakshan** · Available for AI agent and RAG projects on [Upwork](https://www.upwork.com/freelancers/~01483182c29994e5c8)
