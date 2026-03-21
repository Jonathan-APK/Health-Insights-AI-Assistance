# Project Setup & Usage

## 📦 Package Installation
When installing new packages, remember to keep both `pip` and `uv` in sync:
```bash
pip install <package-name>
uv add <package-name>
```

## Run Project Locally
1) Create a `.env` file (ignored by git) with at least the
   following keys as shown in file: `.env.example`
2) Change directory to `/backend`.
3) Run using docker compose
```bash
   docker compose up --build  # rebuilds image first, picks up code changes
```
4) Open html `\sample file\test webpage\test-sse.html` via browser to test server-sent event (SSE) or Swagger UI for non-SSE testing at `http://localhost:8000/docs` when
   `ENV` is **not** set to `production`.

---

## 🔍 Code Quality & SAST Checks

All checks are automatically run in CI via GitHub Actions on every manual trigger. You can also run them locally before pushing. Do take note to resolve these issue before pushing as it will fail the CI checks.

### Prerequisites
Make sure you are in the `/backend` directory and dependencies are installed:
```bash
cd backend
uv sync --frozen --dev
```

### Ruff — Lint & Format

**Check for lint errors:**
```bash
uv run ruff check .
```

**Auto-fix lint errors:**
```bash
uv run ruff check . --fix
```

**Check formatting:**
```bash
uv run ruff format --check .
```

**Auto-fix formatting:**
```bash
uv run ruff format .
```

> Always run both `ruff check --fix` and `ruff format` before pushing to ensure the CI pipeline passes.

---

### Bandit — SAST Security Scan

Bandit scans your Python source code for common security vulnerabilities.

**Run locally:**
```bash
uv run bandit -r . \
  -x ./tests,./venv,./.venv,./env \
  --severity-level medium \
  -f json -o bandit-report.json
```

**View results in terminal (without JSON output):**
```bash
uv run bandit -r . \
  -x ./tests,./venv,./.venv,./env \
  --severity-level medium
```

> The CI pipeline blocks on **medium** severity and above. If Bandit flags an intentional false positive, add `# nosec B<rule-id>` at the end of the flagged line with a comment explaining why.

Example:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104 - required for Docker
```

---

### Safety — Dependency Vulnerability Scan

Safety checks your dependencies against a database of known vulnerabilities.

**Run locally:**
```bash
uv run safety check
```

> Safety runs with `continue-on-error: true` in CI — it will report vulnerabilities but will not block the pipeline. Review the output regularly and update vulnerable dependencies where possible.

---

### Running All Checks at Once
```bash
cd backend

# Lint + format fix
uv run ruff check . --fix
uv run ruff format .

# Verify clean
uv run ruff check .
uv run ruff format --check .

# SAST scan
uv run bandit -r . \
  -x ./tests,./venv,./.venv,./env \
  --severity-level medium

# Dependency scan
uv run safety check
```

---

## Configuration and Deployment Notes
All runtime settings are driven by environment variables defined in
`config/settings.py`. For local development you may create a `.env`
file; be sure **not** to commit it. Use the included
`.env.example` as a template.

In any environment (production, staging, etc.):

* Populate `OPENAI_API_KEY`, `REDIS_URL`, and any other
  fields you need through your platform's secret management system or
  service environment configuration.
* Set `ENV=production` to disable OpenAPI docs and lock down CORS.
* Review the rate‑limit and session TTL settings if you have different
  requirements.

The service itself performs a simple per‑client rate limit and
requires the shared API key on every request; you can layer additional
network or gateway protections as desired. The codebase otherwise
does **not** assume any specific cloud provider or architecture.