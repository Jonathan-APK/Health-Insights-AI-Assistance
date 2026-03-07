# Project Setup & Usage

## 📦 Package Installation
When installing new packages, remember to keep both `pip` and `uv` in sync:
```bash
pip install <package-name>
uv add <package-name>
```
## Run Project Locally
1) Create a `.env` file (ignored by git) with at least the
   following keys:
   ```env
   OPENAI_API_KEY=sk-...
   # optional while developing, the defaults in settings.py are usually
   # fine but you can override them if you want to test production flags
   ENV=local
   REDIS_URL=redis://localhost:6379
   FRONTEND_ORIGINS=http://localhost:3000
   ```
2) Change directory to `/backend`.
3) Run the usual commands:
   ```bash
   uv sync               # keep uv.lock in sync
   uv run python -m spacy download en_core_web_lg
   uv run uvicorn main:app --reload --log-level debug
   ```
4) Ensure a Redis instance is available on the URL above (local
   default is `redis://localhost:6379`).
5) Swagger UI will be visible at http://localhost:8000/docs when
   `ENV` is **not** set to `production`.

### Configuration and deployment notes
All runtime settings are driven by environment variables defined in
`config/settings.py`.  For local development you may create a `.env`
file; be sure **not** to commit it.  Use the included
`.env.example` as a template.

In any environment (production, staging, etc.):

* Populate `OPENAI_API_KEY`, `SHARED_API_KEY`, `REDIS_URL`, and any other
  fields you need through your platform's secret management system or
  service environment configuration.
* Set `ENV=production` to disable OpenAPI docs and lock down CORS.
* Review the rate‑limit and session TTL settings if you have different
  requirements.

The service itself performs a simple per‑client rate limit and
requires the shared API key on every request; you can layer additional
network or gateway protections as desired.  The codebase otherwise
does **not** assume any specific cloud provider or architecture.
