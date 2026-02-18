# 04 — LLM Analyzer

## Background

The digest text needs to be sent to Llama 3.3 70B via Nebius Token Factory (OpenAI-compatible API) and the response parsed into structured JSON.

## Problem

Design an effective system prompt, call the LLM, and reliably extract `{summary, technologies, structure}` from the response — including fallback for malformed JSON.

## Design

### File: `llm_analyzer.py`

```python
async def analyze_repo(digest: str) -> dict:
    """Send digest to LLM and return parsed {summary, technologies, structure}."""
```

**System prompt** (~175 tokens):
```
You are a GitHub repository analyzer. Given repository information, respond with ONLY a JSON object:
{
  "summary": "2-3 sentence description of what the project does and its purpose",
  "technologies": ["list", "of", "key", "technologies"],
  "structure": "1-2 sentence description of the project's code organization"
}
```

**API call**:
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=config.NEBIUS_API_BASE,
    api_key=os.getenv("NEBIUS_API_KEY"),
)

response = await client.chat.completions.create(
    model=config.NEBIUS_MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": digest},
    ],
    max_tokens=config.LLM_MAX_TOKENS,
    temperature=0.2,
)
```

**JSON parsing** with fallback:
1. Try `json.loads(response_text)`
2. If fails, try extracting JSON from markdown code block (```json ... ```)
3. If fails, raise `LLMAnalysisError`

**Validate** that result has all three keys and correct types.

## Implementation Plan

1. Implement `analyze_repo` with OpenAI client setup
2. Implement JSON parsing with fallback extraction
3. Implement response validation
4. Define `LLMAnalysisError` exception

## Trade-offs

- `temperature=0.2`: low for consistency, not 0 to avoid degenerate outputs
- No retry logic — single attempt keeps latency and cost predictable
- `response_format` not used (not guaranteed supported on Nebius) — fallback parsing instead

## Verification Criteria

- Returns valid dict with `summary` (str), `technologies` (list[str]), `structure` (str)
- Handles JSON wrapped in markdown code blocks
- Raises `LLMAnalysisError` on unparseable responses
