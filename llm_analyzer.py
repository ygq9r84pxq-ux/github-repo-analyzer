import json
import os
import re

from openai import AsyncOpenAI

import config

SYSTEM_PROMPT = """You are a GitHub repository analyzer. Given repository information, respond with ONLY a JSON object:
{
  "summary": "2-3 sentence description of what the project does and its purpose",
  "technologies": ["list", "of", "key", "technologies"],
  "structure": "1-2 sentence description of the project's code organization"
}"""


class LLMAnalysisError(Exception):
    pass


def _parse_llm_response(text: str) -> dict:
    """Parse JSON from LLM response, with fallback for markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise LLMAnalysisError(f"Failed to parse LLM response as JSON: {text[:200]}")


def _validate_response(data: dict) -> dict:
    """Validate that response has required keys with correct types."""
    if not isinstance(data.get("summary"), str):
        raise LLMAnalysisError("Missing or invalid 'summary' in LLM response")
    if not isinstance(data.get("technologies"), list):
        raise LLMAnalysisError("Missing or invalid 'technologies' in LLM response")
    if not isinstance(data.get("structure"), str):
        raise LLMAnalysisError("Missing or invalid 'structure' in LLM response")
    # Ensure all technologies are strings
    data["technologies"] = [str(t) for t in data["technologies"]]
    return data


async def analyze_repo(digest: str) -> dict:
    """Send digest to LLM and return parsed {summary, technologies, structure}."""
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise LLMAnalysisError("NEBIUS_API_KEY environment variable not set")

    client = AsyncOpenAI(
        base_url=config.NEBIUS_API_BASE,
        api_key=api_key,
    )

    try:
        response = await client.chat.completions.create(
            model=config.NEBIUS_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": digest},
            ],
            max_tokens=config.LLM_MAX_TOKENS,
            temperature=0.2,
        )
    except Exception as e:
        raise LLMAnalysisError(f"LLM API call failed: {e}")

    text = response.choices[0].message.content.strip()
    data = _parse_llm_response(text)
    return _validate_response(data)
