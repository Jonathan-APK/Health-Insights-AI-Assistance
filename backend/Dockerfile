# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Install dependencies in a separate stage to keep the final image lean.
FROM python:3.12-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching — only re-runs if these change)
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
# --frozen: respect uv.lock exactly, no version resolution
# --no-cache: keep image size down
RUN uv sync --frozen --no-cache --no-dev


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# libmagic1 is the Linux system library that python-magic wraps.
# python-magic-bin (Windows only) must be replaced with this on Linux.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY . .

# Download the spaCy model used by Presidio.
RUN /app/.venv/bin/python -m spacy download en_core_web_md

# Never run as root in production containers
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Make the venv binaries available without full path
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Workers set to 1 — you have one t2.micro; LangGraph state is in-process
# so multiple workers would not share graph state correctly.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
