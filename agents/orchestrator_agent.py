# agents/orchestrator_agent.py

import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.retry_helper import run_with_retry

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.db_tools import log_run, get_recent_runs

load_dotenv()

# ── Import sub-agent ASYNC runner functions ───────────────────────
from agents.ingestion_agent  import run_ingestion_agent_async
from agents.processing_agent import run_processing_agent_async
from agents.analytics_agent  import run_analytics_agent_async


# ── Wrap sub-agents as async tool functions ───────────────────────
async def validate_and_ingest_data(task: str) -> str:
    """
    Runs the Ingestion Agent to validate all ingested Nifty 50 data.
    Use this first to confirm data is loaded and complete.
    Input: a task description string
    """
    return await run_ingestion_agent_async(task)


async def process_and_analyze_data(task: str) -> str:
    """
    Runs the Processing Agent to analyze Silver layer data.
    Use this for sector comparisons, ticker trend analysis,
    top performers by year, and volatility analysis.
    Input: a task description string
    """
    return await run_processing_agent_async(task)


async def generate_insights_report(task: str) -> str:
    """
    Runs the Analytics Agent to generate Gold layer insights.
    Use this to produce full financial reports, anomaly summaries,
    and investment highlights.
    Input: a task description string
    """
    return await run_analytics_agent_async(task)


def get_pipeline_logs() -> dict:
    """Returns recent agent run logs to monitor pipeline status"""
    return {"recent_runs": get_recent_runs(limit=10)}


# ── Orchestrator Agent ────────────────────────────────────────────
orchestrator_agent = Agent(
    name="OrchestratorAgent",
    model="groq/llama-3.3-70b-versatile",
    description="Orchestrates the full Nifty 50 financial insights pipeline",
    instruction="""
        You coordinate a 3-step Nifty 50 financial pipeline:
    1. validate_and_ingest_data — confirm data is loaded
    2. process_and_analyze_data — run requested analysis
    3. generate_insights_report — produce final report

    Run only the steps relevant to the user's request, in order.
    Combine outputs into one response ending with a FINAL SUMMARY.
    If a step fails, note it and continue with remaining steps.
    """,
    tools=[
        validate_and_ingest_data,
        process_and_analyze_data,
        generate_insights_report,
        get_pipeline_logs
    ]
)


async def run_orchestrator_async(task: str) -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="financial_insights",
        user_id="system",
        session_id="orchestrator_session"
    )

    runner = Runner(
        agent=orchestrator_agent,
        app_name="financial_insights",
        session_service=session_service
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=task)]
    )

    async def _run():
        result = ""
        async for event in runner.run_async(
            user_id="system",
            session_id="orchestrator_session",
            new_message=message
        ):
            if hasattr(event, "content") and event.content and event.is_final_response():
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result += part.text
                break
        return result

    result = await run_with_retry(_run)
    log_run("OrchestratorAgent", "success", f"Task: {task}", model="llama-3.3-70b-versatile")
    return result


def run_orchestrator(task: str) -> str:
    return asyncio.run(run_orchestrator_async(task))


if __name__ == "__main__":
    print("Running Full Pipeline via Orchestrator...\n")
    response = run_orchestrator(
        "Run the full pipeline: validate data, analyze the IT sector performance over all years, and generate a 2024 insights report."
    )
    print(response)