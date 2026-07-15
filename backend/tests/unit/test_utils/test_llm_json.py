"""
Unit tests for the LLM JSON extraction helper.

These cover the messy-output cases the Prompt Analyzer depends on: markdown
fences, surrounding prose, braces inside strings, and malformed input.
"""

import pytest

from app.utils.llm_json import extract_json_object


def test_plain_json_object():
    assert extract_json_object('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_json_wrapped_in_markdown_fence():
    text = '```json\n{"a": 1, "b": "x"}\n```'
    assert extract_json_object(text) == {"a": 1, "b": "x"}


def test_json_wrapped_in_bare_fence():
    text = '```\n{"a": 1}\n```'
    assert extract_json_object(text) == {"a": 1}


def test_json_surrounded_by_prose():
    text = 'Sure! Here is the analysis:\n{"a": 1}\nHope that helps.'
    assert extract_json_object(text) == {"a": 1}


def test_braces_inside_string_values():
    text = '{"note": "use {curly} braces here", "n": 2}'
    assert extract_json_object(text) == {"note": "use {curly} braces here", "n": 2}


def test_nested_object_is_extracted_whole():
    text = 'prefix {"a": {"b": 1}} suffix'
    assert extract_json_object(text) == {"a": {"b": 1}}


def test_empty_text_raises():
    with pytest.raises(ValueError):
        extract_json_object("   ")


def test_no_object_raises():
    with pytest.raises(ValueError):
        extract_json_object("there is no json here")


def test_array_is_not_an_object():
    with pytest.raises(ValueError):
        extract_json_object("[1, 2, 3]")


def test_malformed_object_raises():
    with pytest.raises(ValueError):
        extract_json_object('{"a": }')
