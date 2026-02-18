# 03 — Digest Builder

## Background

Raw GitHub data (full tree, full README, many files) exceeds the LLM token budget. This module prunes and assembles a compact digest that maximizes signal per token.

## Problem

Filter the file tree, select high-value files, enforce per-section character budgets, and produce a single text block ready for the LLM.

## Design

### File: `digest_builder.py`

```python
def build_digest(repo_data: dict) -> str:
    """Assemble a budget-constrained text digest from fetched repo data."""
```

**Steps**:

1. **Filter tree** — remove entries matching `IGNORED_DIRS`, `IGNORED_EXTENSIONS`, `IGNORED_FILES` from `config.py`
2. **Render tree string** — depth-capped ASCII tree (4 levels default, 3 for large repos). Truncate to `TREE_CHAR_LIMIT`
3. **Format metadata** — repo description, stars, license, topics, language breakdown. Truncate to `METADATA_CHAR_LIMIT`
4. **Truncate README** — first `README_CHAR_LIMIT` characters
5. **Select & include Tier 2 files** — match filtered tree against `CONFIG_PATTERNS`, fetch contents, pack within `CONFIG_CHAR_LIMIT`
6. **Select & include Tier 3 files** — match against `ENTRY_POINT_PATTERNS`, first 100 lines each, pack within `ENTRY_CHAR_LIMIT`
7. **Assemble** — concatenate labeled sections:

```
## Metadata
{metadata}

## README
{readme}

## Directory Structure
{tree}

## Config Files
{config_contents}

## Entry Points
{entry_contents}
```

### Helper functions

```python
def filter_tree(tree: list[dict]) -> list[dict]
def render_tree(filtered: list[dict], max_depth: int) -> str
def select_files(filtered: list[dict], patterns: list[str]) -> list[str]
def truncate(text: str, limit: int) -> str
```

## Implementation Plan

1. Implement `filter_tree` using config ignore sets
2. Implement `render_tree` with depth cap and char limit
3. Implement `select_files` for Tier 2 and Tier 3 matching
4. Implement `build_digest` orchestrator
5. Test with mock repo data to verify budget compliance

## Trade-offs

- Greedy packing: files are included first-come until budget is full — no optimization for "best" subset
- Tree rendering is simple indented text, not a visual box-drawing style — saves tokens
- README truncation is naive (first N chars) rather than summarizing — keeps this module LLM-free

## Verification Criteria

- Output digest for any repo stays within ~8,000 total characters
- Ignored directories/files are absent from tree
- Tier 2/3 files are correctly identified and included
