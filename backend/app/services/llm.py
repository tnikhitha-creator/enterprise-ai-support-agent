import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

API_URL = "https://router.huggingface.co/hf-inference/models/google/flan-t5-large"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}


def classify_support_message(message):
    prompt = f"""
Classify this customer support message.

Return only this format:
intent: login_issue
priority: high
summary: short summary

Allowed intents:
login_issue, billing_issue, bug_report, feature_request, general_support

Message: {message}
"""

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 100
            }
        },
        timeout=30
    )

    return response.json()
