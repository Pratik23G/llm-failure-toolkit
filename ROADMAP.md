# LLM Failure Toolkit — Roadmap & Session Notes

## End Goal
A **break-point analyser app** — a cross-platform tool (web + iOS + Android) that runs prompts
against multiple LLM agents concurrently, detects where and how models fail, and visualises
failure patterns, latency, and pass rates in a dashboard.

---

## Current Stack (as of Feb 2026)

| Layer | Tech |
|---|---|
| Language | Python 3 |
| Agents | Gemini 2.5 Flash, OpenRouter (google/gemma-3-4b-it:free), StubBot |
| Validators | Empty, Short, Long output (length-only checks) |
| Logging | Append-only JSONL (`data/runs.jsonl`, `data/benchmark_results.jsonl`) |
| Runner | `run.py` — async fan-out CLI, interactive + single-shot |
| Benchmarks | `benchmarks/runner.py` — 10 prompts, per-agent summary printed to terminal |
| Env | `llmenv/` virtualenv, `.env` for API keys |

### API Key status
- **Gemini** — hit free tier RPD limit (20/day). Resets after 24h. Key still valid.
- **OpenRouter** — working. Model: `google/gemma-3-4b-it:free`
- **StubBot** — no key needed, deterministic offline responses

### Run commands (while Gemini is rate-limited)
```bash
source llmenv/Scripts/activate   # Windows/WSL
# or
source llmenv/bin/activate       # macOS/Linux

python run.py --agents stub openai                         # interactive
python run.py --agents stub openai --prompt "your prompt"  # single shot
python -m benchmarks.runner --agents stub openai           # benchmark suite
```

---

## What's Built (Projects 1 & 2)

### Project 1 — Prompt Runner & Logging Harness
- `run.py` — fans out prompts to all agents concurrently with `asyncio.gather`
- `llm/client.py` — `BaseAgent` ABC, `AIBot`, `SecondAIBot`, `StubBot`, `build_registry()`
- `AgentLatencyAnalysis` — rolling p50/p95/p99 latency per agent
- `HandleErrorLogs` — normalises exceptions vs valid responses
- `logger/run_logger.py` — writes one JSON record per run to `data/runs.jsonl`

### Project 2 — Validators & Benchmark Suite
- `validators/base.py` — `contextValidation` dataclass + `BaseValidator` ABC
- `validators/basic_validators.py` — `EmptyOutputValidator`, `ShortOutputValidator`, `LongOutputValidator`
- `validators/runner.py` — `RunAllTests.run_validators()` aggregates pass/fail
- `benchmarks/prompts.json` — 10 prompts (normal, edge-case, failure-trigger)
- `benchmarks/runner.py` — runs all prompts × all agents, saves + prints summary

---

## Planned Architecture

```
┌─────────────────────────────────────┐
│           Frontend                  │
│  Flutter (Web + iOS + Android)      │
└──────────────┬──────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────────┐
│         FastAPI Backend             │
│  /run  /benchmark  /results  /runs  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Existing Python engine          │
│  agents · validators · logger       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        SQLite → PostgreSQL          │
└─────────────────────────────────────┘
```

**Frontend choice: Flutter**
- Single Dart codebase → Web, iOS, Android, Desktop
- Better web support than React Native
- Strong charting libs: fl_chart, syncfusion

---

## Roadmap

### Phase 3 — Real Break-Point Validators `[ ]`
The current validators only catch output length issues. Actual break-points to detect:

- `[ ]` **RepetitionValidator** — flag responses where sentences repeat
- `[ ]` **RefusalValidator** — detect "I can't help", "I'm not able to" patterns
- `[ ]` **ConsistencyValidator** — same prompt across agents, flag diverging answers
- `[ ]` **LatencySpikeValidator** — flag when a run's latency far exceeds the agent's p50
- `[ ]` **HallucinationValidator** — cross-check factual prompts (harder, do last)

Each validator follows the existing `BaseValidator` pattern — just add a new class to
`validators/basic_validators.py` and register it in the runner.

---

### Phase 4 — FastAPI Layer `[ ]` ← next immediate step
Wrap the existing engine with HTTP so any frontend can call it.

Planned endpoints:
```
POST /api/run          — fan-out a prompt to selected agents, return results
POST /api/benchmark    — trigger the benchmark suite (async, stream progress?)
GET  /api/results      — paginated benchmark results
GET  /api/runs         — paginated run history
GET  /api/agents       — list available agents + availability status
```

File to create: `api/main.py`
Dependencies to add: `fastapi`, `uvicorn`, `openai` (already used via OpenRouter)

Run dev server:
```bash
uvicorn api.main:app --reload
```

---

### Phase 5 — Database `[ ]`
Replace JSONL files with a proper DB.

- Local dev: **SQLite** (zero setup, file-based)
- Production: **PostgreSQL**
- ORM: **SQLAlchemy** (maps cleanly to existing dict schemas in `logger/run_logger.py`)

Tables needed:
- `runs` — maps to `data/runs.jsonl` schema
- `benchmark_results` — maps to `data/benchmark_results.jsonl` schema
- `agents` — agent registry + availability status

---

### Phase 6 — Flutter Frontend `[ ]`
Cross-platform UI. Calls the FastAPI backend.

Key screens:
- **Dashboard** — pass rate per agent, avg latency, recent failures (charts)
- **Break-point heatmap** — which prompts fail on which agents (grid view)
- **Live runner** — type a prompt, watch all agents respond in real time
- **Run history** — searchable/filterable log of all runs

---

## File Structure (current + planned)

```
llm-failure-toolkit/
│
├── run.py                        # CLI runner (keep as-is)
├── ROADMAP.md                    # this file
│
├── api/                          # Phase 4 — to be created
│   └── main.py                   # FastAPI app
│
├── llm/
│   └── client.py                 # BaseAgent, AIBot, SecondAIBot, StubBot
│
├── validators/
│   ├── base.py
│   ├── basic_validators.py       # Phase 3 — add new validators here
│   └── runner.py
│
├── benchmarks/
│   ├── prompts.json
│   └── runner.py
│
├── logger/
│   └── run_logger.py             # Phase 5 — swap JSONL writes for DB writes
│
├── data/
│   ├── runs.jsonl
│   └── benchmark_results.jsonl
│
├── frontend/                     # Phase 6 — Flutter project goes here
│
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## Notes
- `ALLOWED_AGENTS` list lives in both `run.py:22` and `benchmarks/runner.py:31` — keep in sync
  when adding new agents
- `StubBot` responses are hardcoded in `llm/client.py:130` — useful for offline testing
- The `openai` agent key actually maps to the OpenRouter/Gemma model (naming is historical)
- Gemini free tier: 20 RPD, 5 RPM on Gemini 2.5 Flash — upgrade to paid or switch model
  to `gemini-2.0-flash` if hitting limits again
