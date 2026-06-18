# tools/retry_helper.py

import asyncio
import re


async def run_with_retry(coro_fn, max_retries=3):
    """
    Runs an async function, automatically retrying on Groq/Gemini rate limit errors.
    Extracts the suggested wait time from the error message and waits that long.
    """
    for attempt in range(max_retries):
        try:
            return await coro_fn()
        except Exception as e:
            error_str = str(e)
            if "rate_limit_exceeded" in error_str or "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                # Try to extract wait time like "try again in 25.41s"
                match = re.search(r"try again in (\d+\.?\d*)s", error_str)
                wait_time = float(match.group(1)) + 2 if match else 15  # +2s buffer

                if attempt < max_retries - 1:
                    print(f"  ⏳ Rate limited. Waiting {wait_time:.0f}s before retry {attempt + 2}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                    continue
            raise  # re-raise if not rate limit, or out of retries

    raise Exception("Max retries exceeded")