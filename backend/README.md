# Project Setup & Usage

## 📦 Package Installation
When installing new packages, remember to keep both `pip` and `uv` in sync:
```bash
pip install <package-name>
uv add <package-name>
```

## Run Langfuse (self-host with docker) Locally [1/4]
0) Install git and Docker Desktop
1) launch Docker Desktop and open its terminal
2) Get a copy of the latest Langfuse repository:
```bash
    git clone https://github.com/langfuse/langfuse.git
```
3) Go into that folder and modify `langfuse\docker-compose.yml`

<br/>Before
```
    services.redis.ports:
                      - 127.0.0.1:6379:6379
```
<br/>After
```
    services.redis.ports:
                      - 127.0.0.1:6380:6379
```

4) Go back to Docker Desktop and start the application
```bash
    cd langfuse
    docker compose up
```

5) Once all the containers are running, open `http://localhost:3000` in your browser


## Setup Langfuse (self-host with docker) Locally [2/4]
0) Ensure your langfuse docker container is running, and open `http://localhost:3000` in your browser

1) Create your account (this account is only tied to the current running langfuse docker) and log in

2) Create "Organization" and "Project" (any naming will do)

3) Go into the created project, scroll through the left side menu and look for "Settings"

4) Click into "Settings", the right panel will be updated. Click into "API Keys"

5) Click the "Create new API keys" button and note down the Public and Secret keys (will be used in the `.env` file based on the updated `.env.example` file)


## Setup Prompt Management in Langfuse (self-host with docker) Locally [3/4]
0) Ensure your langfuse docker container is running, and open `http://localhost:3000` in your browser

1) Log in and go into your working Organization and Project

2) Scroll through the left side menu and look for "Prompts"

3) Click into "Prompts", the right panel will be updated. Click the "New prompt" button

4) Name the prompt as "insights_summary/systemPrompt"

5) In the Prompt section, toggle the setting from 'text' to 'chat' (you will see System role inside the textbox)

6) Copy-paste the entire contents from `backend\prompts\insights_summary\v1.0\summarize.txt`

7) Ensure the checkbox is ticked
```
  Set the "production" label
```

8) Add commit message and then click "Create Prompt" button

## Viewing LLM Tracing in Langfuse (self-host with docker) Locally [4/4]
0) Ensure your langfuse docker container is running, and open `http://localhost:3000` in your browser

1) Log in and go into your working Organization and Project

2) Scroll through the left side menu and look for "Observability/Tracing"

3) Click "Tracing" and then the right panel will be updated

4) Switch from "Traces" to "Observations" view


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

### Backend SIT Scope

Default backend SIT is API smoke coverage only and does not assume the frontend is running.

```bash
pytest tests/SIT/test_api.py
```

Chat route integration coverage is opt-in and should only be run when your integration environment is ready.

```bash
RUN_BACKEND_CHAT_SIT=1 pytest tests/SIT/test_chat_integration.py
```

Use the frontend Playwright SIT suite for browser-driven flows once the frontend is up.

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