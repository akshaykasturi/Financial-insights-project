# test_tools.py — create this in root

from tools.file_tools import (
    get_monthly_summary,
    get_ticker_data,
    get_top_performers_by_year,
    get_anomalies_by_ticker
)
from tools.db_tools import log_run, get_recent_runs

# Test file tools
monthly = get_monthly_summary()
print(f"✅ Monthly summary: {len(monthly)} records")

hdfc = get_ticker_data("HDFCBANK.NS")
print(f"✅ HDFC data: {len(hdfc)} months")

top_2024 = get_top_performers_by_year(2024)
print(f"✅ Top performers 2024: {len(top_2024)} stocks")

anomalies = get_anomalies_by_ticker("HDFCBANK.NS")
print(f"✅ HDFC anomalies: {len(anomalies)} records")

# Test db tools
log_run("TestAgent", "success", "Tools test run", rows=100)
runs = get_recent_runs()
print(f"✅ DB log works: {runs[0]}")