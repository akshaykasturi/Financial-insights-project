# agents/analytics_agent.py

import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.retry_helper import run_with_retry

import litellm
litellm.drop_params = True

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.file_tools import (
    get_top_performers_by_year,
    get_anomaly_summary,
    get_ticker_summary,
    get_sector_summary,
    get_data_overview
)
from tools.db_tools import log_run

load_dotenv()

analytics_agent = Agent(
    name="AnalyticsAgent",
    model="gemini-2.5-flash",
    description="Generates Gold layer financial insights, anomaly reports, and investment summaries",
    instruction="""
    You are a senior financial analytics agent for Nifty 50 market data.
    Your job is to generate actionable insights from the Gold layer data.

    You have these tools available — use them directly, don't ask for clarification:
    - get_top_performers_by_year(year, top_n): gives top N stocks by return for a year
    - get_anomaly_summary(): gives overall anomaly summary across ALL tickers (no ticker needed)
    - get_anomaly_summary(ticker): gives anomaly summary for one specific ticker
    - get_sector_summary(sector): gives yearly stats for one sector
    - get_ticker_summary(ticker): gives yearly stats for one ticker
    - get_data_overview(): gives dataset-wide overview

    For "worst performers": call get_top_performers_by_year with a high top_n (e.g. 50),
    then identify the stocks with the LOWEST yearly_return from those results yourself.

    For "major anomalies" with no specific ticker mentioned: call get_anomaly_summary()
    with no arguments — it returns the most anomalous tickers across the dataset.

    For sector highlights: call get_sector_summary() for each major sector you want
    to compare, like IT, Financials, Pharma, Energy.

    Never ask the user for clarification — make reasonable assumptions and proceed.
    Always produce a complete report with all requested sections.
    Format your output as a proper financial report with clear sections.
    Never fabricate data — only report what the tools return.
    """,
    tools=[
        get_top_performers_by_year,
        get_anomaly_summary,
        get_ticker_summary,
        get_sector_summary,
        get_data_overview
    ]
)


async def run_analytics_agent_async(task: str) -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="financial_insights",
        user_id="system",
        session_id="analytics_session"
    )

    runner = Runner(
        agent=analytics_agent,
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
            session_id="analytics_session",
            new_message=message
        ):
            if hasattr(event, "content") and event.content and event.is_final_response():
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result += part.text
                break
        return result

    result = await run_with_retry(_run)
    log_run("AnalyticsAgent", "success", f"Task: {task}", model="gemini-2.5-flash")
    return result


def run_analytics_agent(task: str) -> str:
    return asyncio.run(run_analytics_agent_async(task))


if __name__ == "__main__":
    print("Running Analytics Agent...\n")
    response = run_analytics_agent(
        "Generate a full financial insights report for 2024 — top performers, worst performers, sector highlights, and major anomalies."
    )
    print(response)