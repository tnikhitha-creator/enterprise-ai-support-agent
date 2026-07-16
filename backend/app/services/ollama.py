from __future__ import annotations

import json
import os
import re
from typing import Any

import ollama
import requests

GROQ_MODEL = "llama-3.1-8b-instant"


ALLOWED_INTENTS = {
    "login_issue",
    "billing_issue",
    "network_issue",
    "bug_report",
    "feature_request",
    "security_issue",
    "general_support",
}

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


def extract_first_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in the LLM response.")

    result = json.loads(match.group())

    if not isinstance(result, dict):
        raise ValueError("LLM response must be a JSON object.")

    return result


def apply_business_rules(
    result: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    lowered = message.lower()

    network_terms = (
        "vpn",
        "wifi",
        "wi-fi",
        "network",
        "internet",
        "dns",
        "connection",
        "connectivity",
    )

    login_terms = (
        "login",
        "password",
        "account locked",
        "cannot access my account",
        "sign in",
    )

    billing_terms = (
        "billing",
        "payment",
        "invoice",
        "charged",
        "refund",
        "subscription",
    )

    security_terms = (
        "phishing",
        "malware",
        "suspicious email",
        "security incident",
        "data breach",
        "compromised",
    )

    bug_terms = (
        "bug",
        "error",
        "crash",
        "not working",
        "failed",
        "broken",
    )

    critical_terms = (
        "production down",
        "system down",
        "service unavailable",
        "all users",
        "company-wide",
        "critical",
        "urgent",
        "outage",
    )

    matched_by_rule = False

    if any(term in lowered for term in security_terms):
        result.update(
            intent="security_issue",
            priority="critical",
            requires_ticket=True,
        )
        matched_by_rule = True

    elif any(term in lowered for term in network_terms):
        result.update(
            intent="network_issue",
            priority="high",
            requires_ticket=True,
        )
        matched_by_rule = True

    elif any(term in lowered for term in login_terms):
        result.update(
            intent="login_issue",
            priority="high",
            requires_ticket=True,
        )
        matched_by_rule = True

    elif any(term in lowered for term in billing_terms):
        result.update(
            intent="billing_issue",
            priority="medium",
            requires_ticket=True,
        )
        matched_by_rule = True

    elif any(term in lowered for term in bug_terms):
        result.update(
            intent="bug_report",
            priority="high",
            requires_ticket=True,
        )
        matched_by_rule = True

    if any(term in lowered for term in critical_terms):
        result["priority"] = "critical"
        result["requires_ticket"] = True
        matched_by_rule = True

    result["matched_by_rule"] = matched_by_rule

    return result


def normalize_classification(
    result: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    intent = str(result.get("intent", "general_support")).lower()
    priority = str(result.get("priority", "medium")).lower()
    summary = str(result.get("summary", message)).strip()
    requires_ticket = bool(result.get("requires_ticket", False))

    if intent not in ALLOWED_INTENTS:
        intent = "general_support"

    if priority not in ALLOWED_PRIORITIES:
        priority = "medium"

    normalized = {
        "intent": intent,
        "priority": priority,
        "summary": summary or message,
        "requires_ticket": requires_ticket,
    }

    normalized = apply_business_rules(normalized, message)
    matched_by_rule = normalized.pop("matched_by_rule")

    if result.get("classification_error"):
        classification_method = "fallback_error"
        confidence = 20
    elif matched_by_rule:
        classification_method = "business_rule"
        confidence = 90
    else:
        classification_method = "llm_only"
        confidence = 60

    normalized["classification_method"] = classification_method
    normalized["confidence"] = confidence

    return normalized


def _chat_with_ollama(prompt: str) -> str:
    response = ollama.chat(
        model="llama3.2:1b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0,
            "num_predict": 150,
        },
    )

    return response["message"]["content"].strip()


def _chat_with_groq(prompt: str, api_key: str) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
            "max_tokens": 150,
        },
        timeout=30,
    )
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


def classify_with_llama(message: str) -> dict[str, Any]:
    prompt = f"""
You classify enterprise support requests.

Choose exactly one intent:
- login_issue
- billing_issue
- network_issue
- bug_report
- feature_request
- security_issue
- general_support

Priority must be one of:
- low
- medium
- high
- critical

Return only valid JSON using this structure:
{{
  "intent": "network_issue",
  "priority": "high",
  "summary": "Short, clear summary",
  "requires_ticket": true
}}

Request:
{message}
"""

    try:
        groq_api_key = os.getenv("GROQ_API_KEY")

        if groq_api_key:
            content = _chat_with_groq(prompt, groq_api_key)
        else:
            content = _chat_with_ollama(prompt)

        result = extract_first_json(content)

    except Exception as exc:
        result = {
            "intent": "general_support",
            "priority": "medium",
            "summary": message,
            "requires_ticket": False,
            "classification_error": str(exc),
        }

    return normalize_classification(result, message)
