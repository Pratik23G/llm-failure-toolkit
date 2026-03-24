# LLM Failure Analysis & Debugging Toolkit

A multi-layer system for running prompts against LLMs, logging structured results, processing logs with a multithreaded C++ binary, and serving everything through a cached REST API.

---

## Architecture

```
                         ┌─────────────────────────────────┐
                         │         Client / Browser         │
                         └────────────┬────────────────────┘
                                      │  HTTP
                                      ▼
                         ┌─────────────────────────────────┐
                         │     FastAPI Server (Python)      │
                         │                                  │
                         │  GET /health                     │
                         │  GET /process-logs?file=...      │
                         └────┬───────────────┬────────────┘
                              │               │
                   ┌──────────▼──┐    ┌───────▼──────────┐
                   │    Redis    │    │  C++ log_processor│
                   │   (cache)   │    │  (subprocess)     │
                   │             │    │                   │
                   │ SHA-256 key │    │ 4 threads, mutex  │
                   │ TTL: 1 hour │    │ reads .jsonl      │
                   └─────────────┘    └───────┬──────────┘
                                              │
                                      ┌───────▼──────────┐
                                      │  data/runs.jsonl  │
                                      │  (structured logs)│
                                      └──────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │                    Prompt Runner (CLI)                       │
  │                                                             │
  │  run.py ──► LLM Agents (Gemini, OpenAI, Stub)             │
  │         ──► Validators (Empty, Short, Long output)          │
  │         ──► Logger ──► data/runs.jsonl                      │
  │                                                             │
  │  benchmarks/runner.py ──► Same pipeline × 10 prompts        │
  └─────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. CLI runner fans out prompts to multiple LLM agents concurrently
2. Each response is validated, timed, and logged to `data/runs.jsonl`
3. The FastAPI server wraps the C++ binary to query log stats over HTTP
4. Redis caches results keyed by file content hash (auto-invalidates on new data)

---

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/Pratik23G/llm-failure-toolkit.git
cd llm-failure-toolkit

# 2. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 3. Build and run
docker compose up --build

# 4. Test the API
curl http://localhost:8000/health
curl http://localhost:8000/process-logs
```

The first `curl` returns service health. The second runs the C++ log processor against `data/runs.jsonl` and returns line counts (cached on repeat calls).

---

## Quick Start (Local, no Docker)

```bash
# 1. Create virtual environment
python -m venv llmenv
source llmenv/bin/activate    # Windows: llmenv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Compile the C++ binary
g++ -O2 -pthread -o cpp/log_processor cpp/log_processor.cpp

# 4. Start Redis (must be running locally)
redis-server

# 5. Configure environment
cp .env.example .env
# Edit .env — set REDIS_URL=redis://localhost:6379/0

# 6. Start the API server
uvicorn api.main:app --reload

# 7. Run prompts (generates data/runs.jsonl)
python run.py --prompt "Hello" --agents stub
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check — reports Redis and C++ binary status |
| `GET` | `/process-logs` | Run log processor. Query param: `?file=path/to/file.jsonl` |
| `GET` | `/docs` | Auto-generated Swagger UI (FastAPI built-in) |

### Example responses

**`GET /health`**
```json
{
  "status": "healthy",
  "dependencies": {
    "redis": "connected",
    "cpp_binary": "found"
  }
}
```

**`GET /process-logs`**
```json
{
  "total_lines": 847,
  "error_lines": 23,
  "cache": "miss"
}
```
On the second call with the same file: `"cache": "hit"` — Redis serves the result instantly without re-running the binary.

---

## CLI Usage

### Interactive mode
```bash
python run.py
```

### Single-shot prompt
```bash
python run.py --prompt "What is the capital of France?"
```

### Select agents
```bash
python run.py --prompt "Hello" --agents gemini stub
python run.py --prompt "Hello" --agents stub          # offline, no API key needed
```

### Run benchmarks
```bash
python -m benchmarks.runner                            # all agents
python -m benchmarks.runner --agents stub              # offline only
python -m benchmarks.runner --agents gemini --timeout 30
```

---

## Project Structure

```
llm-failure-toolkit/
├── api/
│   └── main.py              # FastAPI server, Redis caching, /health endpoint
├── cpp/
│   ├── log_processor.cpp    # Multithreaded C++ log parser (4 threads, mutex)
│   └── log_processor        # Compiled binary (gitignored)
├── llm/
│   └── client.py            # BaseAgent, AIBot (Gemini), SecondAIBot (OpenAI), StubBot
├── validators/
│   ├── base.py              # contextValidation dataclass + BaseValidator ABC
│   ├── basic_validators.py  # Empty, Short, Long output validators
│   └── runner.py            # RunAllTests aggregate runner
├── benchmarks/
│   ├── prompts.json         # 10 predefined benchmark prompts
│   └── runner.py            # Benchmark suite with per-agent reporting
├── logger/
│   └── run_logger.py        # Append-only JSONL logger
├── data/
│   ├── runs.jsonl           # Runtime logs (gitignored)
│   └── benchmark_results.jsonl
├── run.py                   # CLI prompt runner
├── Dockerfile               # Multi-stage build (GCC → Python slim)
├── docker-compose.yml       # App + Redis orchestration
├── requirements.txt
├── .env.example
└── README.md
```

---

## How the Caching Works

```
Request ──► Hash file content (SHA-256) ──► Redis lookup
                                               │
                                     ┌─────────┴─────────┐
                                     │                    │
                                   HIT                  MISS
                                     │                    │
                              Return cached         Run C++ binary
                              result instantly       Parse output
                                                    Store in Redis
                                                    (TTL: 1 hour)
                                                    Return result
```

The cache key is derived from the **file content**, not the file path. This means:
- If you append new log lines → new hash → cache miss → fresh result
- If the file hasn't changed → cache hit → instant response
- No manual cache invalidation needed

---

## Configuration

All configuration is done through environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_TTL` | `3600` | Cache expiry in seconds |
| `CPP_BINARY_PATH` | `cpp/log_processor` | Path to compiled binary |
| `LOG_FILE_PATH` | `data/runs.jsonl` | Default log file to process |

---

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI + Uvicorn | Async, auto-docs, type-safe, production-ready |
| Cache | Redis 7 | In-memory speed, TTL support, industry standard |
| Log Processing | C++ (std::thread, mutex) | Raw speed for line counting, multithreaded |
| LLM Clients | Gemini, OpenAI-compatible | Multi-model comparison |
| Containerisation | Docker + Compose | Reproducible builds, one-command deploy |

---

## License

MIT
