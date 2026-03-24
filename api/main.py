"""
FastAPI server for the LLM Failure Toolkit.

Wraps the C++ log_processor binary behind a REST API and adds Redis caching
so repeated queries against the same log file don't re-run the binary.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LLM Failure Toolkit API",
    version="1.0.0",
    description="REST API for log processing, vector search, and LLM analysis",
)

# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------
# We read the URL from an env var so Docker Compose and local dev can both
# work without code changes.  Default points at a local Redis instance.

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds, default 1 hour

redis_client: redis.Redis | None = None


@app.on_event("startup")
async def _connect_redis():
    """
    Why an event hook instead of module-level?
    ─────────────────────────────────────────
    If Redis is down at import time, a module-level connection would crash the
    entire process.  By deferring to startup we can let the app boot and
    gracefully degrade (cache misses still work, they just hit the binary).
    """
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except redis.ConnectionError:
        redis_client = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CPP_BINARY = os.getenv("CPP_BINARY_PATH", "cpp/log_processor")
LOG_FILE = os.getenv("LOG_FILE_PATH", "data/runs.jsonl")


def _cache_key(file_path: str) -> str:
    """
    Build a cache key from the file content hash.

    Why hash the *content* instead of the file path?
    ─────────────────────────────────────────────────
    If the user appends new log lines, the path stays the same but the data
    changes.  Hashing the content means we automatically bust the cache when
    the file is modified — no manual invalidation needed.
    """
    content = Path(file_path).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    return f"logproc:{digest}"


def _run_cpp_processor(file_path: str) -> dict:
    """
    Shell out to the C++ binary and parse its stdout.

    The binary prints two lines:
        Total lines: 123
        Error lines: 45
    """
    result = subprocess.run(
        [CPP_BINARY, file_path],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"log_processor failed: {result.stderr.strip()}",
        )

    # Parse "Total lines: N" / "Error lines: N"
    parsed = {}
    for line in result.stdout.strip().splitlines():
        key, _, value = line.partition(":")
        parsed[key.strip().lower().replace(" ", "_")] = int(value.strip())

    return parsed


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """
    /health — liveness + dependency check
    ──────────────────────────────────────
    Production load balancers (ALB, k8s readiness probes, etc.) hit this
    endpoint.  We return the status of each dependency so operators can
    diagnose issues without SSH-ing into the container.
    """
    redis_ok = False
    if redis_client:
        try:
            redis_ok = redis_client.ping()
        except redis.ConnectionError:
            pass

    cpp_exists = Path(CPP_BINARY).is_file()

    status = "healthy" if (redis_ok and cpp_exists) else "degraded"

    return {
        "status": status,
        "dependencies": {
            "redis": "connected" if redis_ok else "unavailable",
            "cpp_binary": "found" if cpp_exists else "missing",
        },
    }


@app.get("/process-logs")
async def process_logs(
    file: str = Query(default=None, description="Path to a .jsonl log file"),
):
    """
    Run the C++ log_processor on the given file and return line counts.

    Results are cached in Redis keyed by the SHA-256 of the file content,
    so identical files are never processed twice within the TTL window.

    Cache flow:
        1. Hash the file content → cache key
        2. Check Redis for that key
        3. HIT  → return cached JSON instantly
        4. MISS → run C++ binary → store result in Redis → return
    """
    target = file or LOG_FILE

    if not Path(target).is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {target}")

    # --- Cache lookup ---
    cache_hit = False
    key = _cache_key(target)

    if redis_client:
        try:
            cached = redis_client.get(key)
            if cached:
                cache_hit = True
                result = json.loads(cached)
                return {**result, "cache": "hit"}
        except redis.ConnectionError:
            pass  # degrade gracefully

    # --- Cache miss: run the binary ---
    result = _run_cpp_processor(target)

    if redis_client:
        try:
            redis_client.setex(key, CACHE_TTL, json.dumps(result))
        except redis.ConnectionError:
            pass

    return {**result, "cache": "miss"}
