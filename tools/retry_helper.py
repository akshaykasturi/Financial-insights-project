# tools/retry_helper.py

import asyncio
import re


async def run_with_retry(coro_fn, max_retries=3, retryable_only=True):
    """
    Runs an async function, automatically retrying on rate limit errors
    AND tool_use_failed errors (which are often transient model formatting issues).

    retryable_only=True means: only retry errors we recognize as safe to retry.
    Anything else fails immediately rather than masking a real bug.
    """
    for attempt in range(max_retries):
        try:
            return await coro_fn()
        except Exception as e:
            error_str = str(e)

            is_rate_limit = (
                "rate_limit_exceeded" in error_str
                or "RESOURCE_EXHAUSTED" in error_str
                or "429" in error_str
            )
            is_tool_use_failed = "tool_use_failed" in error_str

            if not retryable_only or is_rate_limit or is_tool_use_failed:
                if attempt < max_retries - 1:
                    if is_rate_limit:
                        match = re.search(r"try again in (\d+\.?\d*)s", error_str)
                        wait_time = float(match.group(1)) + 5 if match else 15
                        print(f"  ⏳ Rate limited. Waiting {wait_time:.0f}s before retry {attempt + 2}/{max_retries}...")
                        await asyncio.sleep(wait_time)
                    else:
                        # tool_use_failed: brief pause, no need for long wait
                        print(f"  🔧 Tool call formatting issue. Retrying {attempt + 2}/{max_retries}...")
                        await asyncio.sleep(2)
                    continue
            raise

    raise Exception("Max retries exceeded")