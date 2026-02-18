# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Repo Analyzer — a FastAPI service that analyzes public GitHub repos using Llama 3.3 70B on Nebius Token Factory. It fetches repo metadata/files via the GitHub REST API (unauthenticated), builds a token-budget-constrained digest, sends it to the LLM, and returns structured JSON (summary, technologies, structure).

## Commands

```bash
# Install
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000

# Test endpoint
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/expressjs/express"}'
```

## Environment

Copy `.env.example` to `.env` and set `NEBIUS_API_KEY` (from https://tokenfactory.nebius.com).

## Architecture

**Single endpoint**: `POST /summarize` accepts `{"github_url": "..."}`, returns `{"summary", "technologies", "structure"}`.

**Pipeline**: URL parsing → GitHub API fetch → digest building → LLM analysis → JSON response.

**Key modules**:
- `main.py` — FastAPI app and `/summarize` endpoint
- `github_fetcher.py` — GitHub REST API calls (metadata, languages, README, tree, file contents)
- `digest_builder.py` — Filters tree, renders depth-capped structure, assembles tiered content within token budget
- `llm_analyzer.py` — Sends digest to Llama 3.3 70B via Nebius OpenAI-compatible API, parses JSON response
- `config.py` — Constants, ignore patterns, file priority lists, token budget limits

**Content tiering strategy** (in `digest_builder.py` / `config.py`):
- Tier 1 (always): metadata, README, filtered directory tree
- Tier 2 (config files): package.json, requirements.txt, Dockerfile, CI YAMLs, etc.
- Tier 3 (entry points, first 100 lines): main.py, app.py, index.ts, etc.

**Token budget**: ~3,000 tokens/request total (~2,000 digest + ~175 system prompt + 800 output). Each section has a character limit. Large repos (1000+ files) get reduced tree depth.

## Task Tracking

All progress is tracked in `tasks.md` at the project root. Before starting work:
1. Check `tasks.md` for current status and what to work on next
2. Mark tasks `[~]` when starting, `[x]` when done
3. Add new tasks if scope changes during implementation

## Design Log Methodology

This project follows the Design-Log Methodology (see `.claude/rules/design-log.md`). Design logs live in `./design-log/` with an index at `./design-log/index.md`.

**Before implementing any feature**:
1. Check `./design-log/index.md` for existing designs
2. Create a design log first, get approval, then implement
3. During implementation, append "Implementation Results" section — do not modify the original design sections
4. Document any deviations from the original design
