# tools/file_tools.py

import pandas as pd
import os

EXPORTS_DIR = "exports"

def get_data_overview() -> dict:
    """
    Returns a lightweight overview of all datasets.
    Row counts, date ranges, tickers, sectors — no raw rows.
    """
    monthly = pd.read_csv(f"{EXPORTS_DIR}/monthly_summary.csv")
    sector  = pd.read_csv(f"{EXPORTS_DIR}/sector_summary.csv")
    top     = pd.read_csv(f"{EXPORTS_DIR}/top_performers.csv")
    anom    = pd.read_csv(f"{EXPORTS_DIR}/anomalies.csv")

    return {
        "monthly_summary":  {"rows": len(monthly), "tickers": monthly["Ticker"].nunique(), "years": sorted(monthly["year"].unique().tolist())},
        "sector_summary":   {"rows": len(sector),  "sectors": sector["Sector"].unique().tolist()},
        "top_performers":   {"rows": len(top),      "years": sorted(top["year"].unique().tolist())},
        "anomalies":        {"rows": len(anom),     "tickers_with_anomalies": anom["Ticker"].nunique()}
    }

def get_ticker_summary(ticker: str) -> dict:
    """
    Returns yearly aggregated stats for a specific ticker.
    Never returns raw rows.
    """
    df = pd.read_csv(f"{EXPORTS_DIR}/monthly_summary.csv")
    df = df[df["Ticker"].str.upper() == ticker.upper()]
    if df.empty:
        return {"error": f"Ticker {ticker} not found"}

    summary = df.groupby("year").agg(
        avg_close=("avg_close", "mean"),
        total_return=("total_monthly_return", "sum"),
        avg_volatility=("avg_volatility", "mean"),
        extreme_move_days=("extreme_move_days", "sum"),
        bullish_days=("bullish_days", "sum"),
        trading_days=("trading_days", "sum")
    ).round(4).reset_index()

    return {
        "ticker": ticker,
        "company": df["Company_Name"].iloc[0] if "Company_Name" in df.columns else ticker,
        "years_available": summary["year"].tolist(),
        "yearly_stats": summary.to_dict(orient="records")
    }

def get_sector_summary(sector: str) -> dict:
    """
    Returns yearly aggregated stats for a specific sector.
    """
    df = pd.read_csv(f"{EXPORTS_DIR}/sector_summary.csv")
    df = df[df["Sector"].str.lower() == sector.lower()]
    if df.empty:
        return {"error": f"Sector {sector} not found. Available sectors: IT, Financials, Pharma, Energy, FMCG, Automobile, Cement"}

    summary = df.groupby("year").agg(
        avg_daily_return=("avg_daily_return", "mean"),
        avg_volatility=("avg_volatility", "mean"),
        avg_pe_ratio=("avg_pe_ratio", "mean"),
        extreme_moves=("extreme_moves", "sum")
    ).round(4).reset_index()

    return {
        "sector": sector,
        "yearly_stats": summary.to_dict(orient="records")
    }

def get_top_performers_by_year(year: int, top_n: int = 10) -> dict:
    """
    Returns top N stocks by yearly return for a given year.
    """
    df = pd.read_csv(f"{EXPORTS_DIR}/top_performers.csv")
    df = df[df["year"] == year].sort_values("yearly_return", ascending=False).head(top_n)
    if df.empty:
        return {"error": f"No data for year {year}"}

    return {
        "year": year,
        "top_performers": df[["Ticker", "Company_Name", "Sector", "yearly_return", "bullish_pct"]].to_dict(orient="records")
    }

def get_anomaly_summary(ticker: str = None) -> dict:
    """
    Returns anomaly counts — never raw anomaly rows.
    Optionally filter by ticker.
    """
    df = pd.read_csv(f"{EXPORTS_DIR}/anomalies.csv")

    if ticker:
        df = df[df["Ticker"].str.upper() == ticker.upper()]
        if df.empty:
            return {"error": f"No anomalies found for {ticker}"}
        return {
            "ticker": ticker,
            "total_anomalies": len(df),
            "extreme_move_days": int(df["is_extreme_move"].sum()),
            "volume_spike_days": int(df["is_volume_spike"].sum()),
        }

    # Overall summary by ticker
    summary = df.groupby("Ticker").agg(
        total_anomalies=("Ticker", "count"),
        extreme_moves=("is_extreme_move", "sum"),
        volume_spikes=("is_volume_spike", "sum")
    ).reset_index().sort_values("total_anomalies", ascending=False).head(15)

    return {
        "total_anomaly_records": len(df),
        "tickers_affected": df["Ticker"].nunique(),
        "top_anomalous_tickers": summary.to_dict(orient="records")
    }

def get_available_tickers() -> dict:
    """Returns list of all available tickers and sectors"""
    df = pd.read_csv(f"{EXPORTS_DIR}/monthly_summary.csv")
    tickers = df[["Ticker", "Company_Name", "Sector"]].drop_duplicates()
    return {
        "total_tickers": len(tickers),
        "tickers": tickers.to_dict(orient="records"),
        "sectors": df["Sector"].unique().tolist()
    }


def get_latest_snapshot(ticker: str = None) -> dict:
    """
    Returns the most recent live trading data (fetched via yfinance).
    If ticker is provided, filters to that ticker only.
    """
    path = f"{EXPORTS_DIR}/latest_snapshot.csv"
    if not os.path.exists(path):
        return {"error": "No live data has been fetched yet"}

    df = pd.read_csv(path)

    if ticker:
        df = df[df["Ticker"].str.upper() == ticker.upper()]
        if df.empty:
            return {"error": f"No live data found for {ticker}"}

    return {
        "as_of": df["Date"].max(),
        "data": df.to_dict(orient="records")
    }