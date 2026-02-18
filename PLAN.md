# GitHub Repo Analyzer — Implementation Plan

Analyze public GitHub repos via FastAPI + Llama 70B (Nebius Token Factory). Smart pruning ensures we extract maximum insight while staying within token/cost budget ($1 total).

## Project Structure

```
nebius_exam_github_sum/
├── main.py                 # FastAPI app & POST /summarize endpoint
├── github_fetcher.py       # GitHub API integration (unauthenticated)
├── digest_builder.py       # Assembles & prunes repo content into a digest
├── llm_analyzer.py         # Nebius/Llama 70B integration
├── config.py               # Constants, ignore patterns, file priority lists
├── requirements.txt
├── .env.example
└── PLAN.md
```

---

## Strategy: What to Send to the LLM

The core challenge is extracting maximum insight from any repo while keeping LLM input small and cheap. We use a **tiered approach**:

### Tier 1 — Always Fetch (Free / Tiny)

| Source | Signal |
|---|---|
| **GitHub API metadata** | Description, topics, language breakdown, stars, license |
| **README.md** | Project purpose, usage, tech mentions |
| **Directory tree** (filtered, depth-capped) | Structure, framework conventions |

### Tier 2 — Config & Manifest Files (Small, High-Signal)

Pattern-matched from the tree and fetched selectively:
- **Dependency manifests**: `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`, `pom.xml`, `build.gradle`, `composer.json`, `*.csproj`
- **Build/tooling**: `Dockerfile`, `docker-compose.yml`, `Makefile`, `tsconfig.json`, `vite.config.*`, `webpack.config.*`
- **CI/CD**: `.github/workflows/*.yml`
- **Framework markers**: `next.config.js`, `nuxt.config.ts`, `angular.json`

### Tier 3 — Entry Points (If Budget Allows)

- `main.py`, `app.py`, `index.ts`, `server.js`, `main.go`, etc.
- First 100 lines only

### What We Always Ignore

Low-value / high-token items excluded from the tree and never fetched:

- **Directories**: `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, `__pycache__/`, `.next/`, `coverage/`, `target/`, `.venv/`, etc.
- **File types**: images (`.png`, `.jpg`, `.svg`), fonts, media, archives, compiled files, PDFs
- **Lock files**: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, etc.
- **Low-value files**: `.env`, `.gitignore`, `.DS_Store`, `.editorconfig`

---

## Token Budget

Working in characters (~4 chars ≈ 1 token), total target ~6500 tokens:

| Section | Char Limit | ~Tokens |
|---|---|---|
| README | 2,000 | ~500 |
| Directory tree | 2,000 | ~500 |
| Config files | 2,000 | ~500 |
| Entry-point files | 1,500 | ~375 |
| Metadata (always small) | ~500 | ~125 |
| **Total digest** | **~8,000** | **~2,000** |
| System prompt | ~700 | ~175 |
| LLM output (max_tokens) | 800 tokens | 800 |
| **Grand total per request** | | **~3,000** |

At Nebius pricing this gives **hundreds of requests within the $1 budget**.

For large repos (1000+ files), tree depth is reduced from 4 → 3 levels. If the tree still exceeds the budget, it's further reduced and truncated.

---

## Pipeline Flow

```
POST /summarize { "github_url": "https://github.com/owner/repo" }
  │
  ├─ Parse owner/repo from URL
  │
  ├─ Fetch from GitHub (unauthenticated REST API)
  │    ├─ GET /repos/{owner}/{repo}           → metadata
  │    ├─ GET /repos/{owner}/{repo}/languages  → language breakdown
  │    ├─ GET /repos/{owner}/{repo}/readme     → README content
  │    ├─ GET /repos/.../git/trees/{branch}?recursive=1  → full tree
  │    └─ GET /repos/.../contents/{path}       → selected config/entry files
  │
  ├─ Build Digest
  │    ├─ Filter tree (remove ignored dirs/files/extensions)
  │    ├─ Render depth-capped tree string
  │    ├─ Identify & include config files (budget-capped)
  │    ├─ Identify & include entry-point files (budget-capped)
  │    └─ Assemble labeled sections into one text block
  │
  ├─ LLM Analysis
  │    ├─ Send digest to Llama 3.3 70B via Nebius (OpenAI-compatible API)
  │    ├─ System prompt requests JSON with: summary, technologies, structure
  │    └─ Parse JSON from response (with fallback extraction)
  │
  └─ Return structured JSON response
       { "summary": "...", "technologies": [...], "structure": "..." }
```

---

## API Contract

**Endpoint**: `POST /summarize`

**Request**:
```json
{ "github_url": "https://github.com/expressjs/express" }
```

**Response** (`200 OK`):
```json
{
  "summary": "Express is a minimal, flexible Node.js web application framework...",
  "technologies": ["JavaScript", "Node.js", "npm"],
  "structure": "The project follows a standard Node.js package layout with lib/ containing the core framework code..."
}
```

**Errors**:
| Status | Meaning |
|---|---|
| 400 | Invalid GitHub URL |
| 404 | Repository not found |
| 429 | GitHub rate limit exceeded |
| 500 | LLM analysis failed |

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Nebius API key
export NEBIUS_API_KEY=your_key_here

# Start the server
uvicorn main:app --reload --port 8000

# Test
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/expressjs/express"}'
```

---

## Dependencies

- **fastapi** + **uvicorn** — Web framework & ASGI server
- **httpx** — Async HTTP client for GitHub API
- **openai** — OpenAI-compatible SDK for Nebius Token Factory
- **pydantic** — Request/response validation
- **python-dotenv** — Load `.env` files
