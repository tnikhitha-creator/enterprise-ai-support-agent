import pytest

from backend.app.services import ollama as ollama_service
from backend.app.services.ollama import (
    apply_business_rules,
    classify_with_llama,
    extract_first_json,
    normalize_classification,
)


def test_extract_first_json_parses_embedded_object():
    text = 'Sure, here you go: {"intent": "billing_issue", "priority": "high"} thanks'

    result = extract_first_json(text)

    assert result == {"intent": "billing_issue", "priority": "high"}


def test_extract_first_json_raises_without_object():
    with pytest.raises(ValueError):
        extract_first_json("no json here")


@pytest.mark.parametrize(
    "message,expected_intent,expected_priority",
    [
        ("My VPN won't connect to the office network", "network_issue", "high"),
        ("I can't sign in, my account is locked", "login_issue", "high"),
        ("I was charged twice on my last invoice", "billing_issue", "medium"),
        ("The export button crashes with an error every time", "bug_report", "high"),
        ("This looks like a phishing email, possible data breach", "security_issue", "critical"),
    ],
)
def test_business_rules_classify_by_keyword(message, expected_intent, expected_priority):
    result = apply_business_rules({"intent": "general_support", "priority": "low"}, message)

    assert result["intent"] == expected_intent
    assert result["priority"] == expected_priority
    assert result["requires_ticket"] is True


def test_critical_terms_override_priority_even_for_unmatched_intent():
    result = apply_business_rules(
        {"intent": "general_support", "priority": "low"},
        "The system is down company-wide, this is urgent",
    )

    assert result["priority"] == "critical"
    assert result["requires_ticket"] is True


def test_normalize_classification_falls_back_on_invalid_values():
    raw = {"intent": "not_a_real_intent", "priority": "extreme", "summary": ""}

    result = normalize_classification(raw, "Just checking in on my ticket status")

    assert result["intent"] == "general_support"
    assert result["priority"] == "medium"
    assert result["summary"] == "Just checking in on my ticket status"


def test_normalize_classification_keeps_valid_values_and_applies_business_rules():
    raw = {"intent": "general_support", "priority": "low", "summary": "VPN drops constantly"}

    result = normalize_classification(raw, "My VPN drops every few minutes")

    assert result["intent"] == "network_issue"
    assert result["priority"] == "high"
    assert result["requires_ticket"] is True


def test_normalize_classification_high_confidence_when_business_rule_matches():
    raw = {"intent": "general_support", "priority": "low", "summary": "VPN drops constantly"}

    result = normalize_classification(raw, "My VPN drops every few minutes")

    assert result["classification_method"] == "business_rule"
    assert result["confidence"] == 90


def test_normalize_classification_moderate_confidence_when_llm_only():
    raw = {"intent": "feature_request", "priority": "low", "summary": "Add dark mode please"}

    result = normalize_classification(raw, "Add dark mode please")

    assert result["classification_method"] == "llm_only"
    assert result["confidence"] == 60


def test_normalize_classification_low_confidence_on_fallback_error():
    raw = {
        "intent": "general_support",
        "priority": "medium",
        "summary": "Something broke",
        "classification_error": "connection refused",
    }

    result = normalize_classification(raw, "Something broke")

    assert result["classification_method"] == "fallback_error"
    assert result["confidence"] == 20


def test_classify_with_llama_uses_ollama_when_no_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def fake_chat_with_ollama(prompt):
        return '{"intent": "billing_issue", "priority": "high", "summary": "s", "requires_ticket": true}'

    def fail_if_called_groq(prompt, api_key):
        raise AssertionError("Groq should not be called when GROQ_API_KEY is unset")

    monkeypatch.setattr(ollama_service, "_chat_with_ollama", fake_chat_with_ollama)
    monkeypatch.setattr(ollama_service, "_chat_with_groq", fail_if_called_groq)

    result = classify_with_llama("I was charged twice")

    assert result["intent"] == "billing_issue"


def test_classify_with_llama_uses_groq_when_key_is_set(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    def fail_if_called_ollama(prompt):
        raise AssertionError("Ollama should not be called when GROQ_API_KEY is set")

    def fake_chat_with_groq(prompt, api_key):
        assert api_key == "test-key"
        return '{"intent": "billing_issue", "priority": "high", "summary": "s", "requires_ticket": true}'

    monkeypatch.setattr(ollama_service, "_chat_with_ollama", fail_if_called_ollama)
    monkeypatch.setattr(ollama_service, "_chat_with_groq", fake_chat_with_groq)

    result = classify_with_llama("I was charged twice")

    assert result["intent"] == "billing_issue"
