# GitHub Repo Analyzer

A FastAPI service that analyzes public GitHub repositories using Llama 3.3 70B on Nebius Token Factory. Send a repo URL, get back a structured summary with technologies and project structure.

## Setup

```bash
git clone <repo-url> && cd github-repo-analyzer
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your Nebius API key:

```
NEBIUS_API_KEY=your_key_here
```

Get a key at https://tokenfactory.nebius.com.

Run the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/expressjs/express"}'
```

Response:

```json
{
  "summary": "A fast, minimalist web framework for Node.js...",
  "technologies": ["JavaScript", "Node.js", "Express"],
  "structure": "lib/ — core framework code\ntest/ — test suite\n..."
}
```

Errors return `{"status": "error", "message": "..."}` with appropriate HTTP status codes (400, 404, 429, 500).

Private or non-existent repositories return 404 with `"Repository not found or is private"` as there isn't a good way to differentiate between the two.

All response codes (success and failures) can be viewed on the server side as well.

## Model Choice

We use **Llama 3.3 70B** via the Nebius OpenAI-compatible API. It offers strong instruction-following and reliable structured JSON output at the 70B parameter scale, which is sufficient for code comprehension and summarization tasks while staying within Token Factory rate limits.

## Repository Handling Approach

The service uses a **tiered content strategy** to stay within the ~3,000 token budget per request:

1. **Tier 1 (always included)**: repository metadata, README, and a filtered/depth-capped directory tree
2. **Tier 2 (config files)**: package.json, requirements.txt, Dockerfile, CI YAML files
3. **Tier 3 (entry points)**: first 100 lines of main.py, app.py, index.ts, and similar files

Large repos (1,000+ files) get reduced tree depth. Each section has a character limit to prevent any single section from consuming the entire budget. Files matching common ignore patterns (node_modules, .git, build artifacts) are excluded from the tree.
