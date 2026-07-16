import pytest

from backend.app.services.ollama import (
    apply_business_rules,
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
