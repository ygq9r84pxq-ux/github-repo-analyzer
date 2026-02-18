# --- Ignore patterns ---
IGNORED_DIRS: set[str] = {
    "node_modules", "vendor", "dist", "build", ".git", "__pycache__",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "env", ".eggs", "egg-info", ".next", ".nuxt", "out", "target",
    "coverage", ".coverage", "htmlcov",
}

IGNORED_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".lock", ".pdf", ".woff", ".woff2", ".ttf", ".eot",
    ".min.js", ".min.css", ".map",
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
}

IGNORED_FILES: set[str] = {
    ".env", ".DS_Store", ".gitignore", ".editorconfig",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}

# --- Tier 2: config/manifest file patterns ---
CONFIG_PATTERNS: list[str] = [
    "package.json", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Makefile", "CMakeLists.txt",
    ".github/workflows/ci.yml", ".github/workflows/ci.yaml",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "tsconfig.json", "webpack.config.js", "vite.config.ts",
]

# --- Tier 3: entry-point file patterns ---
ENTRY_POINT_PATTERNS: list[str] = [
    "main.py", "app.py", "index.ts", "index.js", "server.js", "server.ts",
    "index.py", "cli.py", "manage.py", "main.go", "main.rs",
    "src/main.py", "src/app.py", "src/index.ts", "src/index.js",
    "src/main.go", "src/main.rs", "src/lib.rs",
    "cmd/main.go",
]

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
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
LLM_MAX_TOKENS = 800
ENTRY_POINT_LINE_LIMIT = 100
