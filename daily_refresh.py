# daily_refresh.py
#
# Fetches the latest trading day's data for all 49 Nifty 50 tickers
# via yfinance (free, no API key) and saves it as a "live snapshot"
# that the dashboard/chatbot can blend with historical data.

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from datetime import datetime

EXPORTS_DIR = "exports"

TICKERS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "BPCL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
    "LTIM.NS", "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS",
    "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS",
    "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATASTEEL.NS", "TCS.NS",
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
]

SECTOR_MAP = {
    "ADANIENT.NS": "Infrastructure", "ADANIPORTS.NS": "Infrastructure",
    "APOLLOHOSP.NS": "Healthcare", "ASIANPAINT.NS": "Consumer Durables",
    "AXISBANK.NS": "Financials", "BAJAJ-AUTO.NS": "Automobile",
    "BAJAJFINSV.NS": "Financials", "BAJFINANCE.NS": "Financials",
    "BHARTIARTL.NS": "Telecom", "BPCL.NS": "Energy",
    "BRITANNIA.NS": "FMCG", "CIPLA.NS": "Pharma",
    "COALINDIA.NS": "Metals", "DIVISLAB.NS": "Pharma",
    "DRREDDY.NS": "Pharma", "EICHERMOT.NS": "Automobile",
    "GRASIM.NS": "Cement", "HCLTECH.NS": "IT",
    "HDFCBANK.NS": "Financials", "HDFCLIFE.NS": "Financials",
    "HEROMOTOCO.NS": "Automobile", "HINDALCO.NS": "Metals",
    "HINDUNILVR.NS": "FMCG", "ICICIBANK.NS": "Financials",
    "INDUSINDBK.NS": "Financials", "INFY.NS": "IT",
    "ITC.NS": "FMCG", "JSWSTEEL.NS": "Metals",
    "KOTAKBANK.NS": "Financials", "LT.NS": "Infrastructure",
    "LTIM.NS": "IT", "M&M.NS": "Automobile",
    "MARUTI.NS": "Automobile", "NESTLEIND.NS": "FMCG",
    "NTPC.NS": "Power", "ONGC.NS": "Energy",
    "POWERGRID.NS": "Power", "RELIANCE.NS": "Energy",
    "SBILIFE.NS": "Financials", "SBIN.NS": "Financials",
    "SHREECEM.NS": "Cement", "SUNPHARMA.NS": "Pharma",
    "TATACONSUM.NS": "FMCG", "TATASTEEL.NS": "Metals",
    "TCS.NS": "IT", "TECHM.NS": "IT",
    "TITAN.NS": "Consumer Durables", "ULTRACEMCO.NS": "Cement",
    "WIPRO.NS": "IT",
}

# Reverse map for company names — yfinance gives us longName, we'll fetch it once
_COMPANY_NAME_CACHE = {}


def get_company_name(ticker: str, yf_ticker_obj) -> str:
    if ticker in _COMPANY_NAME_CACHE:
        return _COMPANY_NAME_CACHE[ticker]
    try:
        name = yf_ticker_obj.info.get("longName", ticker.replace(".NS", ""))
    except Exception:
        name = ticker.replace(".NS", "")
    _COMPANY_NAME_CACHE[ticker] = name
    return name


def fetch_latest_data() -> pd.DataFrame:
    """Pulls the most recent trading day's data for all 49 tickers."""
    rows = []
    failed = []

    for ticker in TICKERS:
        try:
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period="5d")  # buffer for weekends/holidays

            if len(hist) < 2:
                failed.append(ticker)
                continue

            latest = hist.iloc[-1]
            previous = hist.iloc[-2]
            daily_return = (latest["Close"] - previous["Close"]) / previous["Close"]

            rows.append({
                "Date": hist.index[-1].strftime("%Y-%m-%d"),
                "Ticker": ticker,
                "Company_Name": get_company_name(ticker, yf_ticker),
                "Sector": SECTOR_MAP.get(ticker, "Unknown"),
                "Open": round(float(latest["Open"]), 2),
                "High": round(float(latest["High"]), 2),
                "Low": round(float(latest["Low"]), 2),
                "Close": round(float(latest["Close"]), 2),
                "Volume": int(latest["Volume"]),
                "Daily_Return": round(float(daily_return), 6),
                "is_bullish": bool(latest["Close"] > latest["Open"]),
            })
        except Exception as e:
            print(f"  ⚠ Failed for {ticker}: {e}")
            failed.append(ticker)

    print(f"\n✓ Fetched {len(rows)}/{len(TICKERS)} tickers successfully")
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    return pd.DataFrame(rows)


def save_latest_snapshot(df: pd.DataFrame):
    """Saves the latest data as a separate 'live' table — does NOT touch historical CSVs."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    path = f"{EXPORTS_DIR}/latest_snapshot.csv"
    df.to_csv(path, index=False)
    print(f"✓ Saved snapshot to {path}")
    print(f"  As of: {df['Date'].max() if not df.empty else 'N/A'}")
    print(f"  Fetched at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    print("Fetching latest Nifty 50 data via yfinance...\n")
    df = fetch_latest_data()
    if not df.empty:
        save_latest_snapshot(df)
        print("\nSample (first 5 rows):")
        print(df.head().to_string(index=False))
    else:
        print("✗ No data fetched — check ticker list or network connection")