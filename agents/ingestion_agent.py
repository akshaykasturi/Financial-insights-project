

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.retry_helper import run_with_retry

from dotenv import load_dotenv
from google.adk.agents import Agent
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.file_tools import (
    get_data_overview,
    get_ticker_summary,
    get_sector_summary,
    get_top_performers_by_year,
    get_anomaly_summary,
    get_available_tickers
)
from tools.db_tools import log_run


load_dotenv()

# ── Define the Agent ──────────────────────────────────────────────
ingestion_agent = Agent(
    name="IngestionAgent",
    model="groq/llama-3.1-8b-instant",
    description="Validates and reports on ingested Nifty 50 financial data",
    instruction="""
        You are a financial data ingestion validation agent.
        Your job is to:
        1. Load the available Gold layer datasets
        2. Validate they are complete and correct
        3. Report row counts, date ranges, tickers, and sectors covered
        4. Flag any obvious data quality issues
        Be concise and structured in your response.
    """,
    tools=[
        get_data_overview,
        get_available_tickers,
        get_anomaly_summary
    ]
)
# ── Runner Setup ──────────────────────────────────────────────────
async def run_ingestion_agent_async(task: str = "Validate all ingested Nifty 50 data and give a summary report") -> str:

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name="financial_insights",
        user_id="system",
        session_id="ingestion_session"
    )

    runner = Runner(
        agent=ingestion_agent,
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
            session_id="ingestion_session",
            new_message=message
        ):
            if hasattr(event, "content") and event.content and event.is_final_response():
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result += part.text
                break
        return result

    result = await run_with_retry(_run)
    log_run("IngestionAgent", "success", f"Task: {task}", model="llama-3.1-8b-instant")
    return result

def run_ingestion_agent(task:str='Valodate all ingested Nifty 50 data and give a summary report') -> str:
    """Sync wrapper so other modules can call this normally"""
    return asyncio.run(run_ingestion_agent_async(task))

# ── Test it directly ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Running Ingestion Agent...\n")
    response = run_ingestion_agent()
    print(response)