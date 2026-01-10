"""Checkpoint generation and validation logic using Gemini."""

import json
import os
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai

DEFAULT_MODEL = "gemini-2.5-flash"

REQUIRED_FIELDS = {
    "title": "Untitled checkpoint",
    "objective": "Define the goal for this step.",
    "concept": "Key concept involved.",
    "function_signature": "function(arg: type) -> return_type",
    "rules": [],
    "expected_output": "Describe expected behavior or result.",
    "hints": [],
    "test_inputs": [],
    "expected_outputs": [],
    "validation_type": "custom",
}


def _coerce_str(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _coerce_list_str(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_list_any(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def normalize_checkpoint(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    normalized["title"] = _coerce_str(raw.get("title"), REQUIRED_FIELDS["title"])
    normalized["objective"] = _coerce_str(raw.get("objective"), REQUIRED_FIELDS["objective"])
    normalized["concept"] = _coerce_str(raw.get("concept"), REQUIRED_FIELDS["concept"])
    normalized["function_signature"] = _coerce_str(raw.get("function_signature"), REQUIRED_FIELDS["function_signature"])
    normalized["rules"] = _coerce_list_str(raw.get("rules")) or REQUIRED_FIELDS["rules"]
    normalized["expected_output"] = _coerce_str(raw.get("expected_output"), REQUIRED_FIELDS["expected_output"])
    normalized["hints"] = _coerce_list_str(raw.get("hints")) or REQUIRED_FIELDS["hints"]
    normalized["test_inputs"] = _coerce_list_any(raw.get("test_inputs"))
    normalized["expected_outputs"] = _coerce_list_any(raw.get("expected_outputs"))
    normalized["validation_type"] = _coerce_str(raw.get("validation_type"), REQUIRED_FIELDS["validation_type"])
    normalized["index"] = idx
    return normalized


def normalize_checkpoints(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        raw = [raw] if raw is not None else []
    normalized_list = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        normalized_list.append(normalize_checkpoint(item, idx))
    return normalized_list


def build_prompt(problem_statement: str) -> str:
    schema = {
        "title": "Short name of the checkpoint (<= 8 words).",
        "objective": "Student-facing goal for this step.",
        "concept": "Key concept(s) applied here.",
        "function_signature": "Python function signature to implement.",
        "rules": "List of hard constraints.",
        "expected_output": "Describe the expected behavior/output.",
        "hints": "List of helpful hints (<= 3).",
        "test_inputs": "Example inputs to try.",
        "expected_outputs": "Outputs aligned to test_inputs.",
        "validation_type": "One of: structure, correctness, integration, custom.",
    }
    prompt = (
        "You are an instructional designer generating programming checkpoints.\n"
        "Return ONLY valid JSON (no prose) representing a list of checkpoint objects.\n"
        "Each checkpoint must follow this JSON schema: " + json.dumps(schema, indent=2) + "\n"
        "Rules:\n"
        "- 3 to 6 checkpoints total.\n"
        "- Keep titles concise.\n"
        "- Provide actionable rules and hints.\n"
        "- Prefer Pythonic, beginner-friendly guidance.\n"
        "Problem statement:\n" + problem_statement.strip() + "\n"
        "Respond with JSON array only.\n"
    )
    return prompt


def extract_json(text: str) -> Any:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Gemini response was empty; no JSON to parse.")
    fenced = re.search(r"```json\s*(.*?)```", cleaned, re.DOTALL)
    candidate = fenced.group(1) if fenced else cleaned
    candidate = candidate.strip()
    if not candidate:
        raise ValueError("Gemini response missing JSON payload.")
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        snippet = candidate[:300].replace("\n", " ")
        raise ValueError(f"Failed to parse Gemini JSON: {exc}; snippet: {snippet}") from exc


def call_gemini(prompt: str, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL) -> str:
    key = api_key or os.getenv("GEMINI_API_KEY") or ""
    if not key:
        raise ValueError("GEMINI_API_KEY is required. Set env var or pass api_key.")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name, generation_config={"temperature": 0.2})
    response = model.generate_content(prompt)
    if not response or not response.text:
        raise RuntimeError("Empty response from Gemini.")
    return response.text


def generate_checkpoints(problem_statement: str, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL) -> List[Dict[str, Any]]:
    prompt = build_prompt(problem_statement)
    raw_text = call_gemini(prompt, api_key=api_key, model_name=model_name)
    parsed = extract_json(raw_text)
    checkpoints = normalize_checkpoints(parsed)
    if not checkpoints:
        raise ValueError("Gemini returned no checkpoints after parsing.")
    return checkpoints


# Example (will call the API if GEMINI_API_KEY is set).
# problem = "Build a simple to-do list CLI with add, list, and complete commands."
# checkpoints = generate_checkpoints(problem)
# print(json.dumps(checkpoints, indent=2))
