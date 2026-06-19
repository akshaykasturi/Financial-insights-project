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

chatbot_agent = Agent(
    name="ChatbotAgent",
    model="groq/llama-3.1-8b-instant",
    description="RAG-powered chatbot answering natural language questions about Nifty 50 stocks",
    instruction="""
    You are a financial data chatbot for Nifty 50 stock market data (1998-2026).
    Users ask you natural language questions about stocks, sectors, performance, and anomalies.

    For casual greetings or small talk (e.g. "hi", "hello", "how are you", "thanks"),
    respond naturally and briefly WITHOUT calling any search tools. You can mention
    you're ready to help with Nifty 50 stock data questions.

    For actual financial questions, follow this process:
    IMPORTANT — Time period translation:
    Before searching, translate any relative time references into explicit years:
    - "pre-COVID" / "before COVID" = 2018, 2019
    - "post-COVID" / "after COVID" = 2021, 2022, 2023
    - "during COVID" = 2020, 2021
    - "recent" / "lately" = 2024, 2025,2026
    - "last year" = 2025
    Include these explicit years in your search queries so retrieval finds the right data.
    For example, search "pharma sector volatility 2018 2019" for pre-COVID, not just "pharma pre-covid".

    For every question:
    1. Identify any time periods mentioned and translate them to explicit years first
    2. Use search_financial_data with explicit years in the query for general queries
    3. Use search_by_ticker when a specific stock ticker is mentioned
    4. Use search_by_sector when a specific sector is mentioned
    5. If comparing two time periods, run separate searches for EACH period explicitly
       (e.g. one search for "pharma 2018 2019", another for "pharma 2021 2022 2023")
    6. Base your answer ONLY on the retrieved data — never make up numbers
    7. Cite specific numbers and years from the retrieved chunks in your answer
    8. If retrieved data doesn't cover the exact years asked, say so honestly

    Be conversational but precise. This is a chatbot, so keep answers
    focused and not overly long unless the user asks for detail.
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