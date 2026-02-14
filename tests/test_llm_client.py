"""
LLM Client Tests
Validates JSON cleaning, scoring, repetition checks, and fallback behavior.
"""

import json

import pytest

from core import llm_client


def test_clean_json_string_strips_markdown_and_trailing_commas():
    """Reality check: malformed JSON from LLM is cleaned into parseable JSON."""
    raw = "```json\n{ 'response': 'ok', 'scam_detected': True, }\n```"
    cleaned = llm_client.clean_json_string(raw)
    parsed = json.loads(cleaned)
    assert parsed["response"] == "ok"
    assert parsed["scam_detected"] is True


def test_parse_response_json_handles_invalid_input():
    """Reality check: invalid JSON returns None without crashing."""
    assert llm_client.parse_response_json("not-json") is None


def test_calculate_response_quality_scores_json_higher():
    """Reality check: valid JSON responses score higher than plain text."""
    json_response = json.dumps({"response": "hello there, this is a valid response"})
    text_response = "this is a long plain response without json " * 3
    score_json = llm_client.calculate_response_quality(json_response, "openai/gpt-oss-120b")
    score_text = llm_client.calculate_response_quality(text_response, "openai/gpt-oss-120b")
    assert score_json > score_text


def test_get_random_fallback_avoids_immediate_repeats():
    """Reality check: fallback selection avoids repeating already used replies."""
    session_id = "fallback-session"
    llm_client._session_responses[session_id] = llm_client.GENERIC_FALLBACK_MESSAGES[:5]
    response = llm_client.get_random_fallback(session_id)
    assert response not in llm_client.GENERIC_FALLBACK_MESSAGES[:5]


def test_is_repetitive_response_checks_prefix_suffix():
    """Reality check: repetition detection catches similar prefix or suffix patterns."""
    history = [
        {"sender": "agent", "text": "Aapka poora naam kya hai?"},
        {"sender": "agent", "text": "Aapka poora naam kya hai?"},
        {"sender": "agent", "text": "Aapka poora naam kya hai?"}
    ]
    assert llm_client.is_repetitive_response("Aapka poora naam kya hai?", history, "rep-1") is True


def test_call_models_parallel_selects_best(monkeypatch):
    """Reality check: parallel calls return a valid response and model."""
    monkeypatch.setattr(llm_client, "OPENROUTER_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setattr(llm_client, "OPENROUTER_MODEL_2", None)
    monkeypatch.setattr(llm_client, "OPENROUTER_FALLBACK", "google/gemini-2.5-flash-lite")

    def fake_call(messages, model, temperature, max_tokens):
        if model == "openai/gpt-oss-120b":
            return json.dumps({"response": "short"})
        return json.dumps({"response": "this is a longer valid response from fallback"})

    monkeypatch.setattr(llm_client, "call_openrouter", fake_call)
    response, model = llm_client.call_models_parallel([{"role": "user", "content": "Hi"}], timeout_seconds=1)
    parsed = json.loads(response)
    assert model in {"openai/gpt-oss-120b", "google/gemini-2.5-flash-lite"}
    assert parsed["response"] in {"short", "this is a longer valid response from fallback"}
