# smartzen-ai

Python / LangGraph / FastAPI assistant service.

## Getting started
\`\`\`
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
\`\`\`
