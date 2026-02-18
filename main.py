from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from digest_builder import build_digest
from github_fetcher import (
    GitHubFetchError,
    RateLimitError,
    RepoNotFoundError,
    fetch_repo_data,
    parse_github_url,
)
from llm_analyzer import LLMAnalysisError, analyze_repo

app = FastAPI(title="GitHub Repo Analyzer")


# --- Custom exception handlers for {"status": "error", "message": "..."} format ---


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


# --- Models ---


class SummarizeRequest(BaseModel):
    github_url: str


class SummarizeResponse(BaseModel):
    summary: str
    technologies: list[str]
    structure: str


# --- Endpoint ---


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    # Validate URL
    try:
        parse_github_url(request.github_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    # Fetch repo data
    try:
        repo_data = await fetch_repo_data(request.github_url)
    except RepoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError:
        raise HTTPException(status_code=429, detail="GitHub rate limit exceeded")
    except GitHubFetchError as e:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {e}")

    # Build digest
    digest = build_digest(repo_data)

    # Analyze with LLM
    try:
        result = await analyze_repo(digest)
    except LLMAnalysisError as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {e}")

    return result
