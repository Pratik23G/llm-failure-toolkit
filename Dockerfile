# ==========================================================================
# Multi-stage Dockerfile for the LLM Failure Toolkit
# ==========================================================================
#
# WHY MULTI-STAGE?
# ────────────────
# Stage 1 ("builder") installs the full GCC toolchain to compile the C++
# binary.  Stage 2 ("runtime") copies only the compiled binary + Python
# dependencies into a slim image.  This keeps the final image ~300 MB
# instead of ~1.2 GB — faster pulls, smaller attack surface.
#
# ==========================================================================

# ── Stage 1: Compile the C++ log_processor ────────────────────────────────
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY cpp/log_processor.cpp .

# -O2    → production-grade optimisation (faster binary, no debug bloat)
# -pthread → required because the code uses std::thread and std::mutex
RUN g++ -O2 -pthread -o log_processor log_processor.cpp


# ── Stage 2: Python runtime ──────────────────────────────────────────────
FROM python:3.12-slim

# Create a non-root user.
# WHY?  Running as root inside containers is a security anti-pattern.
# If an attacker escapes the app, they land as an unprivileged user.
RUN useradd --create-home appuser

WORKDIR /app

# Copy the compiled C++ binary from stage 1
COPY --from=builder /build/log_processor cpp/log_processor
RUN chmod +x cpp/log_processor

# Install Python dependencies first (layer caching).
# WHY COPY requirements.txt SEPARATELY?
# Docker caches each layer.  If only your Python code changes (not deps),
# Docker skips the slow `pip install` step entirely.  This turns a 60-second
# rebuild into a 2-second rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY api/ api/
COPY llm/ llm/
COPY logger/ logger/
COPY validators/ validators/
COPY benchmarks/ benchmarks/
COPY utils/ utils/
COPY config/ config/
COPY run.py .

# Create data directory (for log files)
RUN mkdir -p data && chown appuser:appuser data

# Switch to non-root user
USER appuser

# Expose the FastAPI default port
EXPOSE 8000

# Health check — Docker and orchestrators use this to know if the
# container is alive.  Fails after 3 retries → container gets restarted.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with uvicorn.
# --host 0.0.0.0  → listen on all interfaces (required inside Docker)
# --workers 2     → spawn 2 worker processes for concurrency
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
