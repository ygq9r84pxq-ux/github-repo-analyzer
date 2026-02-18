# Tasks

## Status Legend
- [ ] Pending
- [~] In Progress
- [x] Completed

---

## Phase 0 — Project Setup
- [x] 0.1 Create `requirements.txt` with all dependencies
- [x] 0.2 Create `config.py` with constants, ignore patterns, file priority lists, token budgets
- [x] 0.3 Create `README.md` with setup instructions, model choice rationale, and repo handling approach

## Phase 1 — GitHub Fetcher
- [x] 1.1 Implement `github_fetcher.py` — parse URL, fetch metadata, languages, README, tree, file contents
- [x] 1.2 Handle error cases (invalid URL, 404, rate limiting)

## Phase 2 — Digest Builder
- [x] 2.1 Implement `digest_builder.py` — tree filtering, depth-capping, tiered content assembly
- [x] 2.2 Implement token budget enforcement per section

## Phase 3 — LLM Analyzer
- [x] 3.1 Implement `llm_analyzer.py` — Nebius OpenAI-compatible API integration
- [x] 3.2 System prompt design and JSON response parsing with fallback

## Phase 4 — FastAPI Endpoint
- [x] 4.1 Implement `main.py` — POST /summarize endpoint wiring the full pipeline
- [x] 4.2 Error handling and HTTP status codes (400, 404, 429, 500) — errors must return `{"status": "error", "message": "..."}` format via custom exception handlers

## Phase 5 — Integration & Testing
- [x] 5.1 End-to-end test with a real GitHub repo
- [x] 5.2 Verify token budget stays within limits
