# 01 — Project Setup & Config

## Background

The project needs a shared configuration module and dependency manifest before any feature work begins. All other modules depend on constants defined here.

## Problem

Centralize ignore patterns, file priority lists, and token budget limits so that `github_fetcher.py` and `digest_builder.py` share the same configuration without duplication.

## Design

### `requirements.txt`

```
fastapi>=0.110
uvicorn>=0.29
httpx>=0.27
openai>=1.14
pydantic>=2.6
python-dotenv>=1.0
```

### `config.py`

```python
# --- Ignore patterns ---
IGNORED_DIRS: set[str]   # node_modules, vendor, dist, build, .git, __pycache__, etc.
IGNORED_EXTENSIONS: set[str]  # .png, .jpg, .svg, .lock, .pdf, etc.
IGNORED_FILES: set[str]  # .env, .DS_Store, .gitignore, .editorconfig

# --- Tier 2: config/manifest file patterns ---
CONFIG_PATTERNS: list[str]  # package.json, requirements.txt, Dockerfile, etc.

# --- Tier 3: entry-point file patterns ---
ENTRY_POINT_PATTERNS: list[str]  # main.py, app.py, index.ts, server.js, etc.

# --- Token budget (in characters, ~4 chars ≈ 1 token) ---
README_CHAR_LIMIT = 2000
TREE_CHAR_LIMIT = 2000
CONFIG_CHAR_LIMIT = 2000
ENTRY_CHAR_LIMIT = 1500
METADATA_CHAR_LIMIT = 500

# --- Tree rendering ---
DEFAULT_TREE_DEPTH = 4
LARGE_REPO_THRESHOLD = 1000  # file count
LARGE_REPO_TREE_DEPTH = 3

# --- LLM ---
NEBIUS_API_BASE = "https://api.studio.nebius.com/v1/"
NEBIUS_MODEL = "meta-llama/Meta-Llama-3.3-70B-Instruct"
LLM_MAX_TOKENS = 800
ENTRY_POINT_LINE_LIMIT = 100
```

## Implementation Plan

1. Create `requirements.txt`
2. Create `config.py` with all constants above
3. Verify imports work: `python -c "import config"`

## Trade-offs

- All budgets are hardcoded constants rather than env vars — keeps it simple, easy to tune later if needed
- Using `set` for ignore patterns gives O(1) lookup during tree filtering

## Verification Criteria

- `pip install -r requirements.txt` succeeds
- `python -c "from config import IGNORED_DIRS, TREE_CHAR_LIMIT"` works
