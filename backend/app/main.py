from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.agents.orchestrator import run_support_agent


app = FastAPI()


class SupportMessage(BaseModel):
    email: str
    message: str


def generate_response(agent_result: dict):
    customer = agent_result["customer"]
    ai_result = agent_result["ai_classification"]
    knowledge = agent_result["knowledge_base"]
    jira_result = agent_result["jira"]

    name = customer["name"]
    intent = ai_result["intent"]
    summary = ai_result["summary"]
    source = knowledge["source"]

    if jira_result and jira_result.get("created"):
        ticket_text = f"A Jira ticket has been created: {jira_result['ticket_id']}."
    else:
        ticket_text = "No Jira ticket was created."

    return (
        f"Hi {name}, your request was classified as {intent}. "
        f"Summary: {summary}. "
        f"I found guidance from {source}. "
        f"{ticket_text}"
    )


@app.get("/")
def home():
    return {"status": "AI Support Agent is running with Agent Orchestrator, Llama, RAG, and Jira"}


@app.post("/support")
def support_agent(input_data: SupportMessage):
    agent_result = run_support_agent(input_data.email, input_data.message)
    response = generate_response(agent_result)

    return {
        "input": {
            "email": input_data.email,
            "message": input_data.message
        },
        "agent_result": agent_result,
        "output": response
    }
