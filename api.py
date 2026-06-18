# api.py

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator_agent import run_orchestrator_async
from agents.chatbot_agent import run_chatbot_async
from agents.ingestion_agent import run_ingestion_agent_async
from agents.processing_agent import run_processing_agent_async
from agents.analytics_agent import run_analytics_agent_async
from tools.db_tools import get_recent_runs, get_token_usage_today

app = FastAPI(title="Financial Insights API")

# Allow Streamlit (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ─────────────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default_session"


# ── Health Check ──────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "service": "Financial Insights API"}


# ── Full Pipeline Endpoint ──────────────────────────────────────────
@app.post("/pipeline/run")
async def run_pipeline(request: TaskRequest):
    """Runs the full orchestrator pipeline (Ingestion -> Processing -> Analytics)"""
    try:
        result = await run_orchestrator_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Individual Agent Endpoints (optional, for granular control) ────
@app.post("/agents/ingestion")
async def run_ingestion(request: TaskRequest):
    try:
        result = await run_ingestion_agent_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/processing")
async def run_processing(request: TaskRequest):
    try:
        result = await run_processing_agent_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/analytics")
async def run_analytics(request: TaskRequest):
    try:
        result = await run_analytics_agent_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Chatbot (RAG) Endpoint ───────────────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    """RAG-powered chatbot endpoint"""
    try:
        result = await run_chatbot_async(request.question, request.session_id)
        return {"status": "success", "answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Monitoring Endpoints ─────────────────────────────────────────────
@app.get("/logs/recent")
async def recent_logs(limit: int = 10):
    """Returns recent agent run logs"""
    return {"logs": get_recent_runs(limit)}


@app.get("/logs/usage")
async def token_usage():
    """Returns today's token usage by model"""
    return get_token_usage_today()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)