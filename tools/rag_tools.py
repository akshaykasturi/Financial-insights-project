# tools/rag_tools.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import search


def search_financial_data(query: str, n_results: int = 5) -> dict:
    """
    Search the financial knowledge base using natural language.
    Use this for any question about stock performance, sectors,
    anomalies, or trends that isn't covered by other specific tools.

    Args:
        query: natural language question, e.g. "HDFC performance in 2023"
        n_results: number of relevant chunks to retrieve (default 5)
    """
    results = search(query, n_results=n_results)

    if not results:
        return {"error": "No relevant data found for this query"}

    return {
        "query": query,
        "results_found": len(results),
        "relevant_data": results
    }


def search_by_ticker(query: str, ticker: str, n_results: int = 5) -> dict:
    """
    Search the knowledge base filtered to a specific ticker.

    Args:
        query: natural language question
        ticker: stock ticker e.g. "HDFCBANK.NS"
        n_results: number of chunks to retrieve
    """
    results = search(query, n_results=n_results, ticker_filter=ticker)

    if not results:
        return {"error": f"No data found for {ticker} matching this query"}

    return {
        "query": query,
        "ticker": ticker,
        "relevant_data": results
    }


def search_by_sector(query: str, sector: str, n_results: int = 5) -> dict:
    """
    Search the knowledge base filtered to a specific sector.

    Args:
        query: natural language question
        sector: sector name e.g. "IT", "Financials", "Pharma"
        n_results: number of chunks to retrieve
    """
    results = search(query, n_results=n_results, sector_filter=sector)

    if not results:
        return {"error": f"No data found for {sector} matching this query"}

    return {
        "query": query,
        "sector": sector,
        "relevant_data": results
    }