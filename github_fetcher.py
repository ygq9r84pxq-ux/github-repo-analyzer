import asyncio
import base64
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from config import CONFIG_PATTERNS, ENTRY_POINT_PATTERNS, IGNORED_DIRS


# --- Custom exceptions ---

class GitHubFetchError(Exception):
    pass


class RepoNotFoundError(GitHubFetchError):
    pass


class RateLimitError(GitHubFetchError):
    pass


# --- Data container ---

@dataclass
class RepoData:
    owner: str
    repo: str
    metadata: dict = field(default_factory=dict)
    languages: dict = field(default_factory=dict)
    readme: str | None = None
    tree: list[dict] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)


GITHUB_API = "https://api.github.com"


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL. Raises ValueError on invalid input."""
    parsed = urlparse(url)
    if parsed.hostname not in ("github.com", "www.github.com"):
        raise ValueError(f"Not a GitHub URL: {url}")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {url}")
    owner, repo = parts[0], parts[1]
    # Strip .git suffix
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _check_response(resp: httpx.Response) -> None:
    """Raise appropriate exception for error responses."""
    if resp.status_code == 404:
        raise RepoNotFoundError("Repository not found or is private")
    if resp.status_code == 403 and "X-RateLimit-Remaining" in resp.headers:
        if resp.headers["X-RateLimit-Remaining"] == "0":
            raise RateLimitError("GitHub API rate limit exceeded")
    if resp.status_code >= 400:
        raise GitHubFetchError(f"GitHub API error: {resp.status_code}")


async def fetch_repo_metadata(client: httpx.AsyncClient, owner: str, repo: str) -> dict:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
    _check_response(resp)
    return resp.json()


async def fetch_languages(client: httpx.AsyncClient, owner: str, repo: str) -> dict:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages")
    if resp.status_code == 404:
        return {}
    _check_response(resp)
    return resp.json()


async def fetch_readme(client: httpx.AsyncClient, owner: str, repo: str) -> str | None:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/readme")
    if resp.status_code == 404:
        return None
    _check_response(resp)
    data = resp.json()
    if data.get("encoding") == "base64" and data.get("content"):
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return None


async def fetch_tree(client: httpx.AsyncClient, owner: str, repo: str, default_branch: str) -> list[dict]:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1")
    if resp.status_code == 404:
        return []
    _check_response(resp)
    data = resp.json()
    return data.get("tree", [])


async def fetch_file_content(client: httpx.AsyncClient, owner: str, repo: str, path: str) -> str | None:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}")
    if resp.status_code == 404:
        return None
    _check_response(resp)
    data = resp.json()
    if data.get("encoding") == "base64" and data.get("content"):
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return None


async def fetch_repo_data(github_url: str) -> RepoData:
    """Fetch all repository data. Raises RepoNotFoundError, RateLimitError, or GitHubFetchError."""
    owner, repo = parse_github_url(github_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Metadata first (need default_branch)
        metadata = await fetch_repo_metadata(client, owner, repo)
        default_branch = metadata.get("default_branch", "main")

        # Parallel: languages, readme, tree
        languages, readme, tree = await asyncio.gather(
            fetch_languages(client, owner, repo),
            fetch_readme(client, owner, repo),
            fetch_tree(client, owner, repo, default_branch),
        )

        # Identify Tier 2/3 files to fetch
        all_patterns = set(CONFIG_PATTERNS + ENTRY_POINT_PATTERNS)
        paths_to_fetch = []
        for entry in tree:
            if entry.get("type") != "blob":
                continue
            path = entry.get("path", "")
            # Skip ignored dirs
            if any(p in IGNORED_DIRS for p in path.split("/")):
                continue
            basename = path.split("/")[-1]
            if basename in all_patterns or path in all_patterns:
                paths_to_fetch.append(path)

        # Fetch file contents in parallel
        file_contents = {}
        if paths_to_fetch:
            results = await asyncio.gather(
                *[fetch_file_content(client, owner, repo, p) for p in paths_to_fetch]
            )
            for path, content in zip(paths_to_fetch, results):
                if content is not None:
                    file_contents[path] = content

        return RepoData(
            owner=owner,
            repo=repo,
            metadata=metadata,
            languages=languages,
            readme=readme,
            tree=tree,
            file_contents=file_contents,
        )
