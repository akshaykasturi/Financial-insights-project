# api.py

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from daily_refresh import fetch_latest_data, save_latest_snapshot

from agents.orchestrator_agent import run_orchestrator_async
from agents.chatbot_agent import run_chatbot_async
from agents.ingestion_agent import run_ingestion_agent_async
from agents.processing_agent import run_processing_agent_async
from agents.analytics_agent import run_analytics_agent_async
from tools.db_tools import log_run,get_recent_runs, get_token_usage_today

from dashboard_router import router as dashboard_router

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY","change-this-secret")

def verify_admin(x_admin_key:str = Header(None)):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401,detail="Unauthorized")

app = FastAPI(title="Financial Insights API")

app.include_router(dashboard_router)

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
async def run_pipeline(request: TaskRequest, _: None = Depends(verify_admin)):
    """Runs the full orchestrator pipeline (Ingestion -> Processing -> Analytics)"""
    try:
        result = await run_orchestrator_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Individual Agent Endpoints (optional, for granular control) ────
@app.post("/agents/ingestion")
async def run_ingestion(request: TaskRequest, _: None = Depends(verify_admin)):
    try:
        result = await run_ingestion_agent_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/processing")
async def run_processing(request: TaskRequest, _: None = Depends(verify_admin)):
    try:
        result = await run_processing_agent_async(request.task)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/analytics")
async def run_analytics(request: TaskRequest, _: None = Depends(verify_admin)):
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
async def recent_logs(limit: int = 10, _: None = Depends(verify_admin)):
    """Returns recent agent run logs"""
    return {"logs": get_recent_runs(limit)}


@app.get("/logs/usage")
async def token_usage(_: None = Depends(verify_admin)):
    """Returns today's token usage by model"""
    return get_token_usage_today()

@app.post("/admin/refresh-data")
async def refresh_data(_: None = Depends(verify_admin)):
    """Triggers a fresh pull of live Nifty 50 data via yfinance."""
    try:
        df = fetch_latest_data()
        if df.empty:
            raise HTTPException(status_code=500, detail="No data could be fetched")
        save_latest_snapshot(df)
        log_run(
            "LiveDataRefresh",
            "success",
            f"Refreshed {len(df)} tickers as of {df['Date'].max()}",
            model="yfinance (no LLM)"
        )
        return {
            "status": "success",
            "tickers_fetched": len(df),
            "as_of": df["Date"].max(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)