from config import (
    CONFIG_CHAR_LIMIT,
    CONFIG_PATTERNS,
    DEFAULT_TREE_DEPTH,
    ENTRY_CHAR_LIMIT,
    ENTRY_POINT_LINE_LIMIT,
    ENTRY_POINT_PATTERNS,
    IGNORED_DIRS,
    IGNORED_EXTENSIONS,
    IGNORED_FILES,
    LARGE_REPO_THRESHOLD,
    LARGE_REPO_TREE_DEPTH,
    METADATA_CHAR_LIMIT,
    README_CHAR_LIMIT,
    TREE_CHAR_LIMIT,
)
from github_fetcher import RepoData


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... (truncated)"


def filter_tree(tree: list[dict]) -> list[dict]:
    """Remove entries matching ignore patterns."""
    filtered = []
    for entry in tree:
        path = entry.get("path", "")
        parts = path.split("/")
        # Skip if any directory component is ignored
        if any(p in IGNORED_DIRS for p in parts):
            continue
        # Skip ignored files (basename)
        basename = parts[-1]
        if basename in IGNORED_FILES:
            continue
        # Skip ignored extensions
        if any(basename.endswith(ext) for ext in IGNORED_EXTENSIONS):
            continue
        filtered.append(entry)
    return filtered


def render_tree(filtered: list[dict], max_depth: int) -> str:
    """Render a simple indented tree from flat path list."""
    lines = []
    for entry in filtered:
        path = entry.get("path", "")
        depth = path.count("/")
        if depth >= max_depth:
            continue
        indent = "  " * depth
        name = path.split("/")[-1]
        if entry.get("type") == "tree":
            name += "/"
        lines.append(f"{indent}{name}")
    return truncate("\n".join(lines), TREE_CHAR_LIMIT)


def select_files(filtered: list[dict], patterns: list[str]) -> list[str]:
    """Return paths from filtered tree matching the given patterns (basename or full path)."""
    matched = []
    for entry in filtered:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        basename = path.split("/")[-1]
        if basename in patterns or path in patterns:
            matched.append(path)
    return matched


def format_metadata(repo_data: RepoData) -> str:
    meta = repo_data.metadata
    parts = []
    if meta.get("description"):
        parts.append(f"Description: {meta['description']}")
    if meta.get("stargazers_count") is not None:
        parts.append(f"Stars: {meta['stargazers_count']}")
    if meta.get("license") and meta["license"].get("name"):
        parts.append(f"License: {meta['license']['name']}")
    topics = meta.get("topics", [])
    if topics:
        parts.append(f"Topics: {', '.join(topics)}")
    if repo_data.languages:
        langs = ", ".join(f"{k} ({v})" for k, v in list(repo_data.languages.items())[:10])
        parts.append(f"Languages: {langs}")
    return truncate("\n".join(parts), METADATA_CHAR_LIMIT)


def build_digest(repo_data: RepoData) -> str:
    """Assemble a budget-constrained text digest from fetched repo data."""
    filtered = filter_tree(repo_data.tree)
    file_count = sum(1 for e in repo_data.tree if e.get("type") == "blob")

    # Tree depth
    max_depth = DEFAULT_TREE_DEPTH
    if file_count >= LARGE_REPO_THRESHOLD:
        max_depth = LARGE_REPO_TREE_DEPTH

    sections = []

    # Metadata
    metadata_text = format_metadata(repo_data)
    sections.append(f"## Metadata\n{metadata_text}")

    # README
    if repo_data.readme:
        readme_text = truncate(repo_data.readme, README_CHAR_LIMIT)
        sections.append(f"## README\n{readme_text}")

    # Directory structure
    tree_text = render_tree(filtered, max_depth)
    sections.append(f"## Directory Structure\n{tree_text}")

    # Tier 2: Config files
    config_paths = select_files(filtered, CONFIG_PATTERNS)
    if config_paths and repo_data.file_contents:
        config_parts = []
        budget = CONFIG_CHAR_LIMIT
        for path in config_paths:
            content = repo_data.file_contents.get(path)
            if content and budget > 0:
                chunk = f"### {path}\n{content}"
                chunk = truncate(chunk, budget)
                config_parts.append(chunk)
                budget -= len(chunk)
        if config_parts:
            sections.append(f"## Config Files\n" + "\n\n".join(config_parts))

    # Tier 3: Entry points
    entry_paths = select_files(filtered, ENTRY_POINT_PATTERNS)
    if entry_paths and repo_data.file_contents:
        entry_parts = []
        budget = ENTRY_CHAR_LIMIT
        for path in entry_paths:
            content = repo_data.file_contents.get(path)
            if content and budget > 0:
                lines = content.split("\n")[:ENTRY_POINT_LINE_LIMIT]
                trimmed = "\n".join(lines)
                chunk = f"### {path}\n{trimmed}"
                chunk = truncate(chunk, budget)
                entry_parts.append(chunk)
                budget -= len(chunk)
        if entry_parts:
            sections.append(f"## Entry Points\n" + "\n\n".join(entry_parts))

    return "\n\n".join(sections)
