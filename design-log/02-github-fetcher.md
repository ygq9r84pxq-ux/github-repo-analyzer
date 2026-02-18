# 02 — GitHub Fetcher

## Background

The service needs to fetch repository data from GitHub's public REST API without authentication. This module is the sole data source for everything downstream.

## Problem

Fetch metadata, languages, README, recursive file tree, and selected file contents for any public GitHub repo — handling errors (bad URL, 404, rate limits) gracefully.

## Design

### File: `github_fetcher.py`

**URL parsing**:
```python
def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL. Raises ValueError on invalid input."""
```

Accepts: `https://github.com/owner/repo`, `https://github.com/owner/repo/tree/...`, `http://...`, trailing slashes.

**Data fetching** — all functions are `async` using `httpx.AsyncClient`:

```python
async def fetch_repo_metadata(client, owner, repo) -> dict
async def fetch_languages(client, owner, repo) -> dict
async def fetch_readme(client, owner, repo) -> str | None
async def fetch_tree(client, owner, repo) -> list[dict]
async def fetch_file_content(client, owner, repo, path) -> str | None
```

**Orchestrator**:
```python
async def fetch_repo_data(github_url: str) -> RepoData
```

Calls all the above, returns a dataclass/dict with all fetched data. Fetches metadata first (to get default branch), then tree + README + languages concurrently.

### Error handling

| GitHub status | Our behavior |
|---|---|
| 404 | Raise `RepoNotFoundError("Repository not found or is private")` |
| 403 + rate limit header | Raise `RateLimitError` |
| Other 4xx/5xx | Raise `GitHubFetchError` |

### Concurrency

Use `asyncio.gather` for independent requests (metadata first, then README + languages + tree in parallel, then file contents in parallel).

## Implementation Plan

1. Implement `parse_github_url` with URL validation
2. Implement individual fetch functions
3. Implement `fetch_repo_data` orchestrator with concurrent fetching
4. Define custom exception classes

## Trade-offs

- Unauthenticated API: 60 requests/hour limit, but sufficient for the exam scope
- No pagination for tree: GitHub's recursive tree endpoint returns up to 100k entries, enough for any reasonable repo
- `fetch_file_content` uses the Contents API (base64 decode) — limited to 1MB files, which is fine since we only read first 100 lines of entry points

## Verification Criteria

- `parse_github_url` correctly extracts owner/repo from various URL formats
- Fetching a known public repo (e.g., `expressjs/express`) returns populated data
- Invalid URL raises `ValueError`, non-existent or private repo raises `RepoNotFoundError` with message "Repository not found or is private"
