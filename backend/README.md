# Project Setup & Usage

## 📦 Package Installation
When installing new packages, remember to keep both `pip` and `uv` in sync:
```bash
pip install <package-name>
uv add <package-name>
```
## Run Project Locally
1) Create .env file and add OPENAI_API_KEY 
2) Change directory to /backend
3) Run:
```bash 
uv sync
uv run uvicorn main:app --reload --log-level debug
```
4) Ensure local redis is running on port 6379
Testing using Swagger UI: http://localhost:8000/docs