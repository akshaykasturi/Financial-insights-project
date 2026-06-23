# agents/chatbot_agent.py

import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.retry_helper import run_with_retry

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.rag_tools import search_financial_data, search_by_ticker, search_by_sector
from tools.db_tools import log_run

load_dotenv()

from datetime import datetime

chatbot_agent = Agent(
    name="ChatbotAgent",
    model="groq/llama-3.1-8b-instant",
    description="RAG-powered chatbot answering natural language questions about Nifty 50 stocks",
    instruction=f"""
        You are a financial data chatbot for Nifty 50 stock market data (1998-2026).
        Today's date is {datetime.now().strftime("%B %d, %Y")}. Use this to correctly
        interpret "this year", "recent", "lately", "current" etc.

        CASUAL CONVERSATION:
        For greetings or small talk ("hi", "hello", "thanks"), respond naturally and
        briefly WITHOUT calling any search tools.

        TOOL USE — CRITICAL RULE:
        You have access to real tools (search_financial_data, search_by_ticker,
        search_by_sector). ALWAYS call these using the proper function-calling
        mechanism provided to you. NEVER write out a function call as plain text
        in your response (e.g. never output something like 'function=search(...)').
        If you are unsure whether to call a tool, just call it properly — do not
        describe the call in words instead of making it.

        TIME PERIOD TRANSLATION:
        Translate relative time references into explicit years before searching:
        - "pre-COVID" = 2018, 2019
        - "post-COVID" = 2021, 2022, 2023
        - "during COVID" = 2020, 2021
        - "recent" / "lately" / "this year" = {datetime.now().year}, {datetime.now().year - 1}
        - "last year" = {datetime.now().year - 1}
        Include explicit years in your search queries.

        INVESTMENT-STYLE QUESTIONS:
        You may discuss historical patterns and data-backed observations when asked
        about "what to invest in" or similar. When you do:
        1. Base any suggestion STRICTLY on retrieved data (returns, volatility, trends)
        2. ALWAYS include this disclaimer in every such response, not just sometimes:
           "This is based on historical data only, not financial advice. Please
           consult a licensed financial advisor before making investment decisions."
        3. Be specific with numbers and years from the actual retrieved data
        4. NEVER claim certainty about future performance

        WHEN DATA IS INSUFFICIENT:
        If retrieved data doesn't clearly support a confident answer, say so plainly:
        "The available data doesn't give a clear picture for this — here's what I
        did find: [whatever partial data exists]." Do not deflect vaguely or suggest
        the user "run a separate search" — you have the tools, use them yourself
        before giving up.

        DATA LIMITATIONS TO BE HONEST ABOUT:
        The anomaly dataset is a representative sample, not the complete record for
        very high-volume queries. If asked about completeness, mention this honestly.

        GENERAL RULES:
        - Use search_financial_data for general queries
        - Use search_by_ticker when a specific stock ticker is mentioned
        - Use search_by_sector when a specific sector is mentioned
        - Base answers ONLY on retrieved data — never fabricate numbers
        - Cite specific numbers and years from retrieved chunks
        - Be conversational but precise; keep answers focused, not overly long
    """,
    tools=[search_financial_data, search_by_ticker, search_by_sector]
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
    print("Testing RAG Chatbot...\n")

    test_questions = [
        "How did HDFC Bank perform in 2023?",
        "Which sector had the highest volatility?",
        "Were there any anomalies for Tata Steel?"
    ]

    for q in test_questions:
        print(f"Q: {q}")
        print(f"A: {run_chatbot(q)}")
        print("\n" + "="*60 + "\n")