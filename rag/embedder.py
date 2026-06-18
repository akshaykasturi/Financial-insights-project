# rag/embedder.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

EXPORTS_DIR = "exports"
CHROMA_DIR = "rag/chroma_store"

# Use a local embedding model — no API calls, no quota
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def get_chroma_client():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def row_to_text_monthly(row) -> str:
    return (
        f"Ticker: {row['Ticker']} ({row['Company_Name']}), Sector: {row['Sector']}. "
        f"In {int(row['month'])}/{int(row['year'])}: "
        f"average close price was {row['avg_close']}, "
        f"monthly high {row['monthly_high']}, monthly low {row['monthly_low']}, "
        f"average daily return {row['avg_daily_return']}, "
        f"total monthly return {row['total_monthly_return']}, "
        f"average volatility {row['avg_volatility']}, "
        f"average PE ratio {row['avg_pe_ratio']}, "
        f"extreme move days {row['extreme_move_days']}, "
        f"volume spike days {row['volume_spike_days']}, "
        f"bullish days {row['bullish_days']} out of {row['trading_days']} trading days."
    )


def row_to_text_sector(row) -> str:
    return (
        f"Sector: {row['Sector']}. In {int(row['month'])}/{int(row['year'])}: "
        f"average daily return {row['avg_daily_return']}, "
        f"average volatility {row['avg_volatility']}, "
        f"average PE ratio {row['avg_pe_ratio']}, "
        f"extreme moves {row['extreme_moves']}, "
        f"number of tickers in sector {row['num_tickers']}."
    )


def row_to_text_top_performer(row) -> str:
    return (
        f"Ticker: {row['Ticker']} ({row['Company_Name']}), Sector: {row['Sector']}. "
        f"In year {int(row['year'])}: yearly return was {row['yearly_return']}, "
        f"average volatility {row['avg_volatility']}, average PE ratio {row['avg_pe_ratio']}, "
        f"bullish {row['bullish_pct']}% of {row['trading_days']} trading days, "
        f"extreme move days {row['extreme_move_days']}."
    )


def row_to_text_anomaly(row) -> str:
    return (
        f"Anomaly on {row['Date']} for {row['Ticker']} ({row['Company_Name']}, {row['Sector']}): "
        f"Open {row['Open']}, Close {row['Close']}, Daily Return {row['Daily_Return']}, "
        f"Volume {row['Volume']}. Extreme move: {row['is_extreme_move']}. "
        f"Volume spike: {row['is_volume_spike']}. "
        f"Price vs MA50: {row['vs_MA50_signal']}, vs MA200: {row['vs_MA200_signal']}."
    )


def embed_dataset(collection, csv_name, row_to_text_fn, batch_size=200):
    df = pd.read_csv(f"{EXPORTS_DIR}/{csv_name}")
    print(f"Embedding {csv_name} — {len(df)} rows")

    # For anomalies (36k rows), sample to keep it manageable
    if len(df) > 5000:
        df = df.sample(n=5000, random_state=42)
        print(f"  → sampled down to {len(df)} rows for efficiency")

    documents, metadatas, ids = [], [], []

    for idx, row in df.iterrows():
        text = row_to_text_fn(row)
        documents.append(text)
        metadatas.append({
            "source": csv_name,
            "ticker": str(row.get("Ticker", "N/A")),
            "sector": str(row.get("Sector", "N/A")),
        })
        ids.append(f"{csv_name}_{idx}")

    # Insert in batches
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"  → inserted batch {i}-{i+batch_size}")

    print(f"✓ {csv_name} embedded successfully\n")


def build_vector_store():
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name="nifty50_financial_data",
        embedding_function=embedding_function
    )

    if collection.count() > 0:
        print(f"Collection already has {collection.count()} documents.")
        choice = input("Re-embed everything? (y/n): ")
        if choice.lower() != "y":
            print("Skipping embedding.")
            return collection
        client.delete_collection("nifty50_financial_data")
        collection = client.get_or_create_collection(
            name="nifty50_financial_data",
            embedding_function=embedding_function
        )

    embed_dataset(collection, "monthly_summary.csv", row_to_text_monthly)
    embed_dataset(collection, "sector_summary.csv", row_to_text_sector)
    embed_dataset(collection, "top_performers.csv", row_to_text_top_performer)
    embed_dataset(collection, "anomalies.csv", row_to_text_anomaly)

    print(f"✓ Total documents in collection: {collection.count()}")
    return collection


if __name__ == "__main__":
    build_vector_store()