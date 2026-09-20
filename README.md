# SmartZen AI Assistant

> A prototype AI assistant for a university smart-building system. It answers questions about rooms, schedules, building status and campus policies by calling live backend tools through a local LLM.

## Context

Built during my AI/Backend internship at **SmartZen AI** (Cyprus International University), summer 2026, as part of a multi-repo team project (AI service, backend, frontend, infra, E2E).

This repository is an archived copy of the internship **prototype**, shared with permission. It is not the production system: all data, accounts and credentials are seeded test values. My work was on the AI service (`smartzen-ai`).

## What I Built

### Evaluation & safety
- **Agent eval harness.** Built a 60-case golden set (normal, typo, ambiguous, adversarial, no-tool) with a schema validator, a scorecard command, and CI wiring that posts results on every PR (#128, merged in #168).
- **Prompt-injection suite and safety baseline.** Added a 12-attack injection suite, malformed-output handling, and a proposal-scope property test. Cut successful attacks from 6/12 to 2/12, then traced the remaining two to root cause and showed they are not exploitable at the code level (#135).
- **Coverage expansion.** Added proposal-shape and scope tests and extended golden-set coverage (#140).

### Agent & tools
- **Real tool wiring.** Replaced stubbed tools with real backend calls, added failure handling to `run_tool`, built instructor room-context assembly, and tuned the system prompt from 43/60 to 55/60 on the golden set (#133). Along the way, found and reported two defects in the backend service.
- **Typed backend client.** Generated Pydantic models from the team's OpenAPI contract and built a `BackendClient` with a `get_my_schedule` tool, a resilience layer, and a later async conversion after code review (#130, closing #125).
- **Multi-step agent loop (in progress).** Designing a loop-back edge so the model can read tool results and chain calls, capped at 3 per turn.

### Service reliability
- **JWT verification middleware** attaching a typed auth context to each request.
- **Ollama status endpoint and rate limiting** for the assistant API (#124).
- **Cache extraction and dead-code cleanup**, plus config-driven model selection and a uniform error envelope for LLM failures (#165).
- **CI workflow** running ruff, mypy and pytest on every pull request (#155).
- **Test suites** for the Ollama error hierarchy (30 tests, #172) and tool-error hierarchy (31 tests, #173).

### Code review
- Reviewed teammates' PRs, including a 36-file PR (#138) where I traced every gap back to a single stale-branch root cause, and an ingestion-pipeline PR (#186) where I root-caused a long-standing `documentation_search` failure.

## Tech Stack

Python 3.11+ · FastAPI · LangGraph · Ollama (`qwen2.5:3b`, running on a 4 GB GTX 1650) · Pydantic v2 · httpx · PyJWT · PostgreSQL / pgvector · pytest-asyncio · ruff · mypy · GitHub Actions

## Results

Measured against the real backend at `temperature=0`, reproduced before reporting:
- **Golden-set accuracy:** 55 / 60 (91.7%), up from 43 / 60 before prompt tuning.
- **Prompt-injection suite:** 10 / 12 attacks resisted, up from 6 / 12.

## Known Limitations

- **Single tool per answer.** Multi-tool chaining is still in progress.
- **Documentation search under-routes.** The model reliably picks the docs tool only when a question contains words like "policy".
- **Two injection cases still fail at the prompt level.** They are not exploitable in code, but fully closing them likely needs an architectural change rather than more prompt tuning.

## Running Locally

This service isn't standalone. It needs the SmartZen backend and a local Ollama model.

1. Install Ollama and pull the model: `ollama pull qwen2.5:3b`
2. Copy `.env.example` to `.env` and set `BACKEND_API_URL`, `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.
3. Create a virtual environment, install the project with dev tools, and start the API:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   uvicorn app.main:app --reload --port 8000
   ```
4. Run the checks:
   ```bash
   ruff check . && mypy . && pytest -q
   python -m scripts.run_eval
   python -m scripts.prompt_injections
   ```

Note: the Postgres/pgvector Docker Compose setup used during development is not included in this repo.
