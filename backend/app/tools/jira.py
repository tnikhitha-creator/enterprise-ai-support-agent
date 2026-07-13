import os
import requests
from dotenv import load_dotenv


load_dotenv()


def create_jira_ticket(customer: dict, intent: str, message: str):
    jira_domain = os.getenv("JIRA_DOMAIN")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    jira_project_key = os.getenv("JIRA_PROJECT_KEY")

    url = f"{jira_domain}/rest/api/3/issue"

    summary = f"{intent.replace('_', ' ').title()} - {customer['name']}"

    description_text = (
        f"Customer Name: {customer['name']}\n"
        f"Company: {customer['company']}\n"
        f"Plan: {customer['plan']}\n"
        f"Account Status: {customer['status']}\n"
        f"Priority: {customer['priority']}\n\n"
        f"Customer Message:\n{message}"
    )

    payload = {
        "fields": {
            "project": {
                "key": jira_project_key
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description_text
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": "Task"
            }
        }
    }

    response = requests.post(
        url,
        json=payload,
        auth=(jira_email, jira_api_token),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    )

    if response.status_code == 201:
        data = response.json()
        return {
            "created": True,
            "ticket_id": data["key"],
            "ticket_url": f"{jira_domain}/browse/{data['key']}"
        }

    return {
        "created": False,
        "error": response.text,
        "status_code": response.status_code
    }
