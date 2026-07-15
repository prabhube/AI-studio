"""
LLM JSON extraction helpers.

WHY this file exists:
    Language models routinely wrap JSON in markdown fences or surrounding prose
    despite being told not to. Any service that asks an LLM for structured
    output needs to pull the first well-formed JSON object out of a noisy
    completion. Centralising that here keeps every LLM-consuming service simple
    and consistently robust.
"""

from __future__ import annotations

import json
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Extract and parse the first complete JSON object found in ``text``.

    Tolerates common language-model output quirks:
      - Markdown code fences (```json ... ```)
      - Leading/trailing prose around the object
      - Braces that appear inside string values

    Args:
        text: Raw text returned by an LLM.

    Returns:
        The parsed JSON object as a dict.

    Raises:
        ValueError: If no parseable JSON object is present.
    """
    if not text or not text.strip():
        raise ValueError("Empty text: no JSON object to parse.")

    candidate = _strip_code_fences(text.strip())

    # Fast path: the whole payload is already valid JSON.
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    # Fallback: scan for the first balanced, string-aware {...} block.
    snippet = _first_balanced_object(candidate)
    if snippet is None:
        raise ValueError("No JSON object found in text.")

    try:
        result = json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON object: {exc}") from exc

    if not isinstance(result, dict):
        raise ValueError("Extracted JSON is not an object.")
    return result


def _strip_code_fences(text: str) -> str:
    """Remove a surrounding markdown code fence, if present."""
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]  # drop opening ``` or ```json
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]  # drop closing ```
    return "\n".join(lines).strip()


def _first_balanced_object(text: str) -> str | None:
    """
    Return the first balanced ``{...}`` substring, or None if there isn't one.

    Tracks string context so braces inside JSON string values don't throw off
    the depth count.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None
