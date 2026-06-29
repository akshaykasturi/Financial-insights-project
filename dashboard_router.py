# dashboard_api.py
#
# Add these endpoints to your existing api.py (or import this router into it).
# These are PURE DATA endpoints — no LLM/agent calls, no Groq tokens used.
# They read directly from your exports/*.csv files (already on disk).

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

EXPORTS_DIR = "exports"


def _load(name: str) -> pd.DataFrame:
    path = f"{EXPORTS_DIR}/{name}.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{name}.csv not found")
    return pd.read_csv(path)


@router.get("/meta")
async def dashboard_meta():
    """Returns available filter options for the dashboard UI dropdowns."""
    monthly = _load("monthly_summary")
    sectors = sorted(monthly["Sector"].dropna().unique().tolist())
    years = sorted(monthly["year"].dropna().unique().astype(int).tolist())
    tickers = sorted(monthly["Ticker"].dropna().unique().tolist())
    return {
        "sectors": sectors,
        "years": years,
        "tickers": tickers,
    }


@router.get("/sector-comparison")
async def sector_comparison(
    year: int = Query(...),
    metric: str = Query("avg_daily_return", description="avg_daily_return | avg_volatility | avg_pe_ratio")
):
    """Returns one data point per sector for a given year and metric — for bar/line charts."""
    valid_metrics = {"avg_daily_return", "avg_volatility", "avg_pe_ratio"}
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"metric must be one of {valid_metrics}")

    df = _load("sector_summary")
    df = df[df["year"] == year]
    if df.empty:
        return {"year": year, "metric": metric, "data": []}

    grouped = df.groupby("Sector")[metric].mean().round(4).reset_index()
    grouped = grouped.sort_values(metric, ascending=False)

    return {
        "year": year,
        "metric": metric,
        "data": [
            {"sector": row["Sector"], "value": row[metric]}
            for _, row in grouped.iterrows()
        ],
    }


@router.get("/top-performers")
async def top_performers(
    year: int = Query(...),
    top_n: int = Query(10, ge=1, le=50),
    direction: str = Query("best", description="best | worst")
):
    """Returns top or bottom N stocks by yearly return for a given year — for bar charts."""
    df = _load("top_performers")
    df = df[df["year"] == year]
    if df.empty:
        return {"year": year, "data": []}

    ascending = direction == "worst"
    df = df.sort_values("yearly_return", ascending=ascending).head(top_n)

    return {
        "year": year,
        "direction": direction,
        "data": [
            {
                "ticker": row["Ticker"],
                "company": row["Company_Name"],
                "sector": row["Sector"],
                "yearly_return": round(row["yearly_return"], 4),
                "volatility": round(row["avg_volatility"], 4),
            }
            for _, row in df.iterrows()
        ],
    }


@router.get("/ticker-trend")
async def ticker_trend(ticker: str = Query(...)):
    """Returns yearly trend data for one ticker — for line charts over time."""
    df = _load("monthly_summary")
    df = df[df["Ticker"].str.upper() == ticker.upper()]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for ticker {ticker}")

    yearly = df.groupby("year").agg(
        avg_close=("avg_close", "mean"),
        total_return=("total_monthly_return", "sum"),
        avg_volatility=("avg_volatility", "mean"),
    ).round(4).reset_index()

    return {
        "ticker": ticker.upper(),
        "company": df["Company_Name"].iloc[0] if "Company_Name" in df.columns else ticker,
        "data": yearly.to_dict(orient="records"),
    }


@router.get("/sector-trend")
async def sector_trend(sector: str = Query(...)):
    """Returns yearly trend data for one sector — for line charts over time."""
    df = _load("sector_summary")
    df = df[df["Sector"].str.lower() == sector.lower()]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for sector {sector}")

    yearly = df.groupby("year").agg(
        avg_daily_return=("avg_daily_return", "mean"),
        avg_volatility=("avg_volatility", "mean"),
        avg_pe_ratio=("avg_pe_ratio", "mean"),
    ).round(4).reset_index()

    return {
        "sector": sector,
        "data": yearly.to_dict(orient="records"),
    }


@router.get("/overview-stats")
async def overview_stats():
    """Returns headline numbers for the dashboard hero/summary cards."""
    monthly = _load("monthly_summary")
    anomalies = _load("anomalies")

    return {
        "total_tickers": int(monthly["Ticker"].nunique()),
        "total_sectors": int(monthly["Sector"].nunique()),
        "year_range": [int(monthly["year"].min()), int(monthly["year"].max())],
        "total_records": int(len(monthly)),
        "total_anomalies": int(len(anomalies)),
    }

@router.get("/latest-snapshot")
async def latest_snapshot():
    """Returns the most recently fetched live-ish data."""
    path = f"{EXPORTS_DIR}/latest_snapshot.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No live data fetched yet")

    df = pd.read_csv(path)
    return {
        "as_of": df["Date"].max(),
        "data": df.to_dict(orient="records"),
    }