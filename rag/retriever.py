# rag/retriever.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = "rag/chroma_store"

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_collection(
            name="nifty50_financial_data",
            embedding_function=embedding_function
        )
    return _collection


def search(query: str, n_results: int = 5, ticker_filter: str = None, sector_filter: str = None) -> list:
    """
    Search the vector store for relevant financial data chunks.
    """
    collection = get_collection()

    where_clause = {}
    if ticker_filter:
        where_clause["ticker"] = ticker_filter.upper()
    if sector_filter:
        where_clause["sector"] = sector_filter

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause if where_clause else None
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source"),
            "ticker": meta.get("ticker"),
            "sector": meta.get("sector"),
            "relevance_score": round(1 - dist, 3)
        })

    return chunks


if __name__ == "__main__":
    # Quick test
    results = search("HDFC bank performance in 2023", n_results=3)
    for r in results:
        print(r)
        print("---")