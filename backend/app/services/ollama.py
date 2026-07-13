import json
import re
import ollama


def extract_first_json(text: str):
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise json.JSONDecodeError("No JSON found", text, 0)


def apply_business_rules(result: dict, message: str):
    lowered = message.lower()

    if "login" in lowered or "password" in lowered or "account" in lowered or "access" in lowered:
        result["intent"] = "login_issue"
        result["priority"] = "high"
        result["requires_ticket"] = True

    if "billing" in lowered or "payment" in lowered or "invoice" in lowered:
        result["intent"] = "billing_issue"
        result["priority"] = "medium"
        result["requires_ticket"] = True

    if "bug" in lowered or "error" in lowered or "not working" in lowered:
        result["intent"] = "bug_report"
        result["priority"] = "high"
        result["requires_ticket"] = True

    if "critical" in lowered or "urgent" in lowered or "production down" in lowered:
        result["priority"] = "critical"
        result["requires_ticket"] = True

    return result


def classify_with_llama(message: str):
    prompt = f"""
You are a software system that classifies customer support tickets.

This is a safe demo project.

Classify the message into one intent:
login_issue, billing_issue, bug_report, feature_request, general_support

Return EXACTLY ONE JSON object.
Do not return examples.
Do not add explanation.
Do not use markdown.

JSON format:
{{
  "intent": "login_issue",
  "priority": "high",
  "summary": "Short summary",
  "requires_ticket": true
}}

Customer support message:
"{message}"
"""

    response = ollama.chat(
        model="llama3.2:1b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0,
            "num_predict": 120
        }
    )

    content = response["message"]["content"].strip()

    try:
        result = extract_first_json(content)
    except Exception:
        result = {
            "intent": "general_support",
            "priority": "medium",
            "summary": message,
            "requires_ticket": True,
            "raw_llm_response": content
        }

    return apply_business_rules(result, message)
