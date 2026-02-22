# LLM Prompt Runner & Logging Harness
**Pet Project 1 – Foundation for LLM Failure Analysis & Debugging Toolkit**

This repository contains **Project 1** of a multi-stage capstone focused on building an **LLM Failure Analysis & Debugging Toolkit**.

The purpose of this project is to create a **reliable prompt execution engine** and a **structured logging harness** that captures everything needed for downstream analysis (latency, metadata, outputs).

---

## Project Goal

Build a simple but robust system that:

- Runs prompts/tasks against Large Language Models (LLMs)
- Measures execution metadata (timestamps, latency, model info)
- Logs every run in a structured format (JSONL)
- Validates model responses for quality failures
- Serves as the **data backbone** for later failure analysis

---

## Why This Matters

To debug LLM behavior, you must first **observe it**.

This logging harness enables future capabilities such as:
- Failure detection
- Hallucination analysis
- Prompt debugging
- Model comparison
- Automated reporting

---

## Project Components

### Prompt Runner (`run.py`)
- CLI-based prompt execution
- Fans out user prompts to multiple agents **concurrently**
- Measures request timestamp (UTC) and per-agent latency (p50/p95/p99)
- Validates each response and passes all data to the logger

### LLM Client (`llm/client.py`)
- `BaseAgent` ABC — shared interface contract for all agents
- `AIBot` — Google Gemini Flash 2.5 (streaming)
- `SecondAIBot` — Nebius-hosted OpenAI-compatible model
- `StubBot` — offline deterministic agent (no API key required)
- `AgentLatencyAnalysis` — rolling p50/p95/p99 latency tracking
- `HandleErrorLogs` — normalises exceptions vs valid responses
- `build_registry()` — factory that initialises agents after env vars are loaded

### Validators (`validators/`)
- `BaseValidator` — abstract base with shared `build_result()` contract
- `EmptyOutputValidator` — catches blank or whitespace-only responses
- `ShortOutputValidator` — catches responses under 10 characters
- `LongOutputValidator` — catches responses exceeding 300 characters (configurable)
- `RunAllTests` — runs all validators and returns an aggregate pass/fail dict

### Benchmark Runner (`benchmarks/`)
- `prompts.json` — 10 predefined prompts covering normal, edge-case, and failure-trigger scenarios
- `runner.py` — fans out each prompt to all agents, collects validation + latency, writes `data/benchmark_results.jsonl`, and prints a per-agent summary report

### Logging Harness (`logger/run_logger.py`)
- Receives prompt, response, and all metadata
- Writes **one JSON object per run** to `data/runs.jsonl`
- Append-only, JSONL format — easy to ingest for analysis

---

## Project Structure

```
llm-failure-toolkit/
│
├── run.py                    # Main prompt runner (interactive + single-shot)
│
├── llm/
│   └── client.py             # BaseAgent, AIBot, SecondAIBot, StubBot, build_registry
│
├── validators/
│   ├── __init__.py
│   ├── base.py               # contextValidation dataclass + BaseValidator ABC
│   ├── basic_validators.py   # Empty, Short, Long output validators
│   └── runner.py             # RunAllTests — runs all validators, returns aggregate result
│
├── benchmarks/
│   ├── __init__.py
│   ├── prompts.json          # 10 predefined benchmark prompts
│   └── runner.py             # Benchmark runner — reports per-agent pass rates & latency
│
├── logger/
│   └── run_logger.py         # Logging harness — appends to data/runs.jsonl
│
├── data/
│   ├── runs.jsonl            # Runtime logs (gitignored)
│   └── benchmark_results.jsonl  # Benchmark run logs (gitignored)
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/llm-failure-toolkit.git
cd llm-failure-toolkit
```

### 2. Create and activate a virtual environment
```bash
python -m venv llmenv

# Windows
llmenv\Scripts\activate

# macOS / Linux
source llmenv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file and add your API keys:
```
GEMINI_API_KEY=your_gemini_key_here
NEBIUS_API_KEY=your_nebius_key_here
```

---

## CLI Usage

### Interactive mode (loop until `exit`)
```bash
python run.py
```

### Single-shot prompt mode
```bash
python run.py --prompt "What is the capital of France?"
```

### Select specific agents
```bash
python run.py --prompt "Hello" --agents gemini stub
python run.py --prompt "Hello" --agents stub          # offline, no API key needed
```

### Set a custom timeout
```bash
python run.py --prompt "Hello" --timeout 10
```

### Run the benchmark suite
```bash
# All agents (default)
python -m benchmarks.runner

# Offline only (no API keys needed)
python -m benchmarks.runner --agents stub

# Specific agents with custom timeout
python -m benchmarks.runner --agents gemini openai --timeout 30
```

---

## Pet Project 2 — Validator

Validate outputs given by the model, detect failure cases, and store validation results.

**Validators implemented:**
- `EmptyOutputValidator` — flags blank responses
- `ShortOutputValidator` — flags responses under 10 chars
- `LongOutputValidator` — flags responses over 300 chars

**Benchmark suite:** 10 prompts designed to trigger and surface specific failure modes across all agents.
