# 05 — FastAPI Endpoint

## Background

The FastAPI app wires together all modules into a single `POST /summarize` endpoint. This is the user-facing entry point.

## Problem

Accept a GitHub URL, run the full pipeline (fetch → digest → analyze), return structured JSON, and map internal exceptions to appropriate HTTP status codes.

## Design

### File: `main.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="GitHub Repo Analyzer")

class SummarizeRequest(BaseModel):
    github_url: str

class SummarizeResponse(BaseModel):
    summary: str
    technologies: list[str]
    structure: str

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    ...
```

**Error mapping**:

```python
try:
    owner, repo = parse_github_url(request.github_url)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid GitHub URL")

try:
    repo_data = await fetch_repo_data(request.github_url)
except RepoNotFoundError:
    raise HTTPException(status_code=404, detail="Repository not found")
except RateLimitError:
    raise HTTPException(status_code=429, detail="GitHub rate limit exceeded")

digest = build_digest(repo_data)

try:
    result = await analyze_repo(digest)
except LLMAnalysisError:
    raise HTTPException(status_code=500, detail="LLM analysis failed")
```

**Dotenv loading**: `load_dotenv()` at module level to load `NEBIUS_API_KEY`.

## Implementation Plan

1. Define Pydantic request/response models
2. Implement `/summarize` endpoint with full pipeline
3. Map exceptions to HTTP status codes
4. Add `load_dotenv()` at startup

## Trade-offs

- Synchronous dotenv loading at import time — simple, no startup event needed
- No input sanitization beyond URL parsing — GitHub API handles the rest
- No caching — each request fetches fresh data (acceptable for exam scope)

## Error Response Format

The assignment requires error responses in the format `{"status": "error", "message": "..."}`. FastAPI's default `HTTPException` returns `{"detail": "..."}`, so we add custom exception handlers to reformat.

### Exception Handlers

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": "Invalid request body"},
    )
```

- Existing `raise HTTPException(...)` calls remain unchanged — handlers intercept and reformat
- All error responses now return `{"status": "error", "message": "..."}` instead of `{"detail": "..."}`

## Verification Criteria

- `POST /summarize` with valid repo URL returns 200 with `{summary, technologies, structure}`
- Invalid URL returns 400 with `{"status": "error", "message": "Invalid GitHub URL"}`
- Non-existent or private repo returns 404 with `{"status": "error", "message": "Repository not found or is private"}`
- Malformed JSON body returns 400 with `{"status": "error", "message": "Invalid request body"}`
- Server starts with `uvicorn main:app`
