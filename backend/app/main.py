from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.app.agents.orchestrator import run_support_agent
from backend.app.api.admin import router as admin_router

app = FastAPI(
    title="Agent Hub API",
    version="2.0.0",
)
app.include_router(admin_router)

class SupportRequest(BaseModel):
    email: str
    message: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Agent Hub",
    }


@app.post("/support")
def support(request: SupportRequest):
    try:
        agent_result = run_support_agent(
            email=request.email,
            message=request.message,
        )

        final_response = agent_result.get(
            "final_response",
            "The request was processed.",
        )

        return {
            "input": {
                "email": request.email,
                "message": request.message,
            },
            "agent_result": agent_result,
            "output": final_response,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent Hub failed to process the request: {exc}",
        ) from exc
