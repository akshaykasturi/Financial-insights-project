# agents/processing_agent.py

import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os

os.environ["LITELLM_LOG"] = "DEBUG"

from tools.retry_helper import run_with_retry

import litellm
litellm.drop_params = True

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.file_tools import (
    get_ticker_summary,
    get_sector_summary,
    get_top_performers_by_year,
    get_available_tickers
)
from tools.db_tools import log_run

load_dotenv()

processing_agent = Agent(
    name="ProcessingAgent",
    model="groq/llama-3.3-70b-versatile",
    description="Analyzes cleaned Nifty 50 Silver layer data and produces structured insights",
    instruction="""
        You are a financial data processing agent for Nifty 50 stocks.
        When given a task, you:
        1. Use the available tools to fetch relevant data
        2. Analyze trends, compare sectors or tickers
        3. Identify patterns in returns, volatility, and market behavior
        4. Return a clean structured analysis

        Always use tools to get data — never make up numbers.
        Keep responses concise and data-driven.
    """,
    tools=[
        get_ticker_summary,
        get_sector_summary,
        get_top_performers_by_year,
        get_available_tickers
    ]
)


async def run_processing_agent_async(task: str) -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="financial_insights",
        user_id="system",
        session_id="processing_session"
    )

    runner = Runner(
        agent=processing_agent,
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
            session_id="processing_session",
            new_message=message
        ):
            if hasattr(event, "content") and event.content and event.is_final_response():
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result += part.text
                break
        return result

    result = await run_with_retry(_run)
    log_run("ProcessingAgent", "success", f"Task: {task}", model="groq/llama-3.3-70b-versatile")
    return result


def run_processing_agent(task: str) -> str:
    return asyncio.run(run_processing_agent_async(task))


if __name__ == "__main__":
    print("Running Processing Agent...\n")
    response = run_processing_agent(
        "Compare the IT and Financials sectors — which had better average returns and lower volatility over all available years?"
    )
    print(response)