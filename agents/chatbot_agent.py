# agents/chatbot_agent.py

import sys, os, re, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


from tools.file_tools import (
    get_sector_summary,
    get_top_performers_by_year,
    get_ticker_summary,
    get_data_overview,
    get_latest_snapshot
)
from tools.db_tools import log_run
from tools.retry_helper import run_with_retry

load_dotenv()

CURRENT_YEAR = datetime.now().year
CURRENT_DATE_STR = datetime.now().strftime("%B %d, %Y")

MAX_TURNS_KEPT = 2          # how many past exchanges to keep in full
MAX_ANSWER_CHARS = 400      # truncate long past answers to this length when carried forward


chatbot_agent = Agent(
    name="ChatbotAgent",
    model="groq/llama-3.3-70b-versatile",
    description="RAG-powered chatbot answering natural language questions about Nifty 50 stocks",
    instruction=f"""
        You are a financial data chatbot for Nifty 50 stock market data (1998-2026).
        Today's date is {CURRENT_DATE_STR}. Current year is {CURRENT_YEAR}.
        "Recent" means {CURRENT_YEAR-1}-{CURRENT_YEAR}. "Last year" means {CURRENT_YEAR-1}.

        CONVERSATION MEMORY:
        You'll see a short summary of recent exchanges before the current question.
        Use it to understand follow-ups like "I don't like that, suggest something
        else" — refer back to what was discussed without needing the full original
        answer repeated to you.

        CASUAL CONVERSATION:
        For greetings or small talk, respond naturally WITHOUT calling any tools.

        TOOL USE — CRITICAL RULE:
        Always call tools using the proper function-calling mechanism. NEVER write
        out a function call as plain text in your response (e.g. never output
        something like "<function=tool_name>{{...}}</function>" as visible text).
        If you decide to use a tool, use the actual function-calling mechanism —
        do not narrate or describe the call in your response text.

        PARAMETER NAMING — EXACT MATCH REQUIRED:
        Tool parameters are case-sensitive and must match EXACTLY as defined:
        - get_sector_summary(sector: str)  — use lowercase "sector", NOT "Sector"
        - get_ticker_summary(ticker: str)   — use lowercase "ticker"
        - get_top_performers_by_year(year: int, top_n: int)
        - get_data_overview() takes NO parameters — call with empty arguments

        CHOOSING THE RIGHT TOOL:
        1. AGGREGATE TOOLS (prefer for general/vague questions):
           get_data_overview, get_sector_summary, get_top_performers_by_year,
           get_ticker_summary

        Always try AGGREGATE tools first for general questions.

        TIME PERIOD TRANSLATION:
        - "pre-COVID" = 2018, 2019 | "post-COVID" = 2021, 2022, 2023
        - "recent"/"lately"/"this year" = {CURRENT_YEAR}, {CURRENT_YEAR-1}

        INVESTMENT-STYLE QUESTIONS:
        1. Base suggestions STRICTLY on retrieved data
        2. ALWAYS include: "This is based on historical data only, not financial
           advice. Please consult a licensed financial advisor before making
           investment decisions."
        3. Never claim future certainty

        LIVE DATA:
        For questions about "yesterday", "today", "latest price", "current
        price", or "most recent" data — use get_latest_snapshot instead of
        the historical aggregate tools. This returns near-real-time prices
        (fetched via yfinance), separate from the historical 1998-2026 dataset.
        If asked for a specific stock's latest price, pass the ticker parameter.
        When reporting live/recent price data (not investment suggestions),
        you do NOT need the historical-data disclaimer — just state the date
        and price clearly, e.g. "As of [date], the closing price was ₹X."
        Only use the investment disclaimer when actually discussing where to
        invest or comparing performance for decision-making purposes.
        IMPORTANT: get_ticker_summary and other aggregate tools return YEARLY
        averages across the historical dataset — they do NOT reflect single-day
        or "recent" performance. Never use them to answer questions about
        "yesterday," "today," or "recent days" — only use them for explicit
        year-based or long-term trend questions (e.g., "how did X do in 2023").
        WHEN TOO VAGUE: redirect plainly to ask for a specific stock/sector/year.

        GENERAL RULES:
        - Base answers ONLY on tool data — never fabricate numbers
        - Be conversational but precise; keep answers focused
    """,
    tools=[
        get_data_overview,
        get_sector_summary,
        get_top_performers_by_year,
        get_ticker_summary,
        get_latest_snapshot
    ]
)

# ── Conversation history management — bounded, not unlimited ────────
_conversation_histories = {}   # session_id -> list of (question, answer) tuples


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "... [truncated]"


def _build_context_prefix(session_id: str) -> str:
    """Builds a short context summary from recent turns, bounded in size"""
    history = _conversation_histories.get(session_id, [])
    if not history:
        return ""

    recent = history[-MAX_TURNS_KEPT:]
    lines = ["[Recent conversation context:]"]
    for q, a in recent:
        truncated_answer = _truncate(a, MAX_ANSWER_CHARS)
        lines.append(f"User asked: {q}\nYou answered: {truncated_answer}")
    lines.append("[End of context. Now answer the new question below.]\n")
    return "\n".join(lines)


def _record_turn(session_id: str, question: str, answer: str):
    _conversation_histories.setdefault(session_id, []).append((question, answer))
    if len(_conversation_histories[session_id]) > MAX_TURNS_KEPT * 3:
        _conversation_histories[session_id] = _conversation_histories[session_id][-MAX_TURNS_KEPT*2:]


def _sanitize_answer(text: str) -> str:
    """
    Removes any leaked function-call syntax from the model's final answer,
    and falls back to a clean message if nothing useful remains.
    """
    if not text:
        return "I wasn't able to generate a clear answer for that. Could you rephrase your question?"

    # Strip any <function=...>...</function> or unclosed <function=...> tags
    cleaned = re.sub(r"<function=.*?</function>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<function=.*?>", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    if len(cleaned) < 10:
        return "I had trouble pulling that data together. Could you try asking in a different way — for example, naming a specific sector or stock?"

    return cleaned


# ── Session management — fresh ADK session EVERY call now ───────────
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

    context_prefix = _build_context_prefix(session_id)
    full_input = f"{context_prefix}\n{question}" if context_prefix else question

    message = types.Content(
        role="user",
        parts=[types.Part(text=full_input)]
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

    raw_result = await run_with_retry(_run)
    result = _sanitize_answer(raw_result)
    _record_turn(session_id, question, result)   # store the CLEAN version in history
    log_run("ChatbotAgent", "success", f"Q: {question}", model="groq/llama-3.3-70b-versatile")
    return result


def run_chatbot(question: str, session_id: str = "chat_session") -> str:
    return asyncio.run(run_chatbot_async(question, session_id))


def clear_session(session_id: str):
    """Call this when user wants to start a fresh conversation"""
    _conversation_histories.pop(session_id, None)



# Replace the __main__ block with this:

async def _run_test_conversation():
    sid = "test_conversation_1"

    test_questions = [
        "Recent days performance of reliance"
    ]

    for q in test_questions:
        print(f"Q: {q}")
        answer = await run_chatbot_async(q, session_id=sid)
        print(f"A: {answer}")
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("Testing Chatbot With Bounded Conversation Memory + Sanitization...\n")
    asyncio.run(_run_test_conversation())