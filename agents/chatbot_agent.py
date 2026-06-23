# agents/chatbot_agent.py

import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tools.rag_tools import search_financial_data, search_by_ticker, search_by_sector
from tools.file_tools import (
    get_sector_summary,
    get_top_performers_by_year,
    get_ticker_summary,
    get_data_overview
)
from tools.db_tools import log_run
from tools.retry_helper import run_with_retry

load_dotenv()

CURRENT_YEAR = datetime.now().year
CURRENT_DATE_STR = datetime.now().strftime("%B %d, %Y")

chatbot_agent = Agent(
    name="ChatbotAgent",
    model="groq/llama-3.1-8b-instant",
    description="RAG-powered chatbot answering natural language questions about Nifty 50 stocks",
    instruction=f"""
        You are a financial data chatbot for Nifty 50 stock market data (1998-2026).
        Today's date is {CURRENT_DATE_STR}. Always use this as ground truth for
        interpreting "this year", "recent", "lately", "current", "now" etc.
        Current year is {CURRENT_YEAR}. "Recent" means {CURRENT_YEAR-1}-{CURRENT_YEAR}.
        "Last year" means {CURRENT_YEAR-1}. Never reason about "recent" using old
        years like 2018-2020 unless the user explicitly asks about that period.

        CASUAL CONVERSATION:
        For greetings or small talk ("hi", "hello", "thanks"), respond naturally and
        briefly WITHOUT calling any search tools.

        TOOL USE — CRITICAL RULE:
        Always call tools using the proper function-calling mechanism provided to you.
        NEVER write out a function call as plain text in your response. If unsure
        whether to call a tool, just call it properly — never describe a call in words.

        CHOOSING THE RIGHT TOOL — THIS MATTERS A LOT:
        You have two categories of tools:

        1. AGGREGATE TOOLS (prefer these for general/vague questions):
           - get_data_overview(): dataset-wide stats
           - get_sector_summary(sector): yearly stats for a sector
           - get_top_performers_by_year(year, top_n): best/worst returns for a year
           - get_ticker_summary(ticker): yearly stats for one stock
           Use these for questions like "how's the market", "where should I invest",
           "which sector is doing well", "top stocks this year" — anything needing
           real statistics rather than individual anomaly events.

        2. RAG SEARCH TOOLS (use only for specific lookups):
           - search_financial_data, search_by_ticker, search_by_sector
           Use these ONLY when the user asks about specific anomalies, unusual
           events, or detailed history for a named stock/sector — not for general
           market questions.

        Always try the AGGREGATE tools FIRST for general questions. Only fall back
        to RAG search if aggregate tools genuinely don't cover what's being asked.

        TIME PERIOD TRANSLATION:
        Translate relative time references into explicit years before calling tools:
        - "pre-COVID" = 2018, 2019
        - "post-COVID" = 2021, 2022, 2023
        - "during COVID" = 2020, 2021
        - "recent" / "lately" / "this year" / "now" = {CURRENT_YEAR}, {CURRENT_YEAR-1}
        - "last year" = {CURRENT_YEAR-1}

        INVESTMENT-STYLE QUESTIONS:
        You may discuss historical patterns when asked "what should I invest in" etc.
        1. Base suggestions STRICTLY on retrieved aggregate data (returns, volatility)
        2. ALWAYS include this exact disclaimer in every such response:
           "This is based on historical data only, not financial advice. Please
           consult a licensed financial advisor before making investment decisions."
        3. Be specific with real numbers and years from the actual data
        4. NEVER claim certainty about future performance

        WHEN A QUESTION IS TOO VAGUE EVEN FOR AGGREGATE TOOLS:
        If a question genuinely has no clear scope (no sector, ticker, or year
        implied, even after reasonable interpretation), say so plainly and redirect:
        "I can give you solid answers about a specific stock, sector, or year —
        could you narrow it down? For example: 'How is the IT sector doing in 2025?'
        or 'Top performing stocks in 2024?'"
        Do NOT call RAG search tools repeatedly hoping for a relevant random result
        when the question is this vague — redirect instead.

        GENERAL RULES:
        - Base answers ONLY on retrieved/tool data — never fabricate numbers
        - Cite specific numbers and years from tool results
        - Be conversational but precise; keep answers focused, not overly long
    """,
    tools=[
        get_data_overview,
        get_sector_summary,
        get_top_performers_by_year,
        get_ticker_summary,
        search_financial_data,
        search_by_ticker,
        search_by_sector
    ]
)


async def run_chatbot_async(question: str, session_id: str = "chat_session") -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="financial_insights",
        user_id="user",
        session_id=session_id
    )

    runner = Runner(
        agent=chatbot_agent,
        app_name="financial_insights",
        session_service=session_service
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=question)]
    )

    async def _run():
        result = ""
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=message
        ):
            if hasattr(event, "content") and event.content and event.is_final_response():
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result += part.text
                break
        return result

    result = await run_with_retry(_run)
    log_run("ChatbotAgent", "success", f"Q: {question}", model="llama-3.1-8b-instant")
    return result


def run_chatbot(question: str) -> str:
    return asyncio.run(run_chatbot_async(question))


if __name__ == "__main__":
    print("Testing Updated RAG Chatbot...\n")

    test_questions = [
        "hey",
        "what is the best place to invest with 1 lakh",
        "how is the market doing recently",
        "can you base it on data from this year"
    ]

    for q in test_questions:
        print(f"Q: {q}")
        print(f"A: {run_chatbot(q)}")
        print("\n" + "="*60 + "\n")