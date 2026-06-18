# Agents for Financial Data Processing — Nifty 50

A multi-agent AI system for processing, analyzing, and querying Nifty 50 stock market data,
built on Databricks (Medallion Architecture), Google ADK, ChromaDB (RAG), FastAPI, and Streamlit.

## Architecture

\`\`\`
Raw Nifty 50 Data (Kaggle)
        ↓
Databricks (PySpark)
Bronze → Silver → Gold (Delta Tables)
        ↓
Exported to local CSVs
        ↓
┌─────────────────────────────────────────┐
│           AI Agent Layer (ADK)            │
│                                            │
│  Orchestrator Agent (llama-3.3-70b)       │
│   ├── Ingestion Agent  (llama-3.1-8b)     │
│   ├── Processing Agent (llama-3.1-8b)     │
│   └── Analytics Agent  (llama-3.3-70b)    │
│                                            │
│  Chatbot Agent (RAG, llama-3.1-8b)        │
│   └── ChromaDB Vector Store                │
└─────────────────────────────────────────┘
        ↓
FastAPI Backend
        ↓
Streamlit Frontend (Pipeline Dashboard + Chat + Logs)
\`\`\`

## Tech Stack

- **Data Engineering:** Databricks, PySpark, Delta Lake
- **AI Agents:** Google ADK, Groq (Llama 3.1 8B / 3.3 70B)
- **RAG:** ChromaDB, sentence-transformers (all-MiniLM-L6-v2)
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Storage:** SQLite (agent run logs)

## Project Structure

\`\`\`
financial_insights/
├── agents/              # 5 AI agents
├── tools/                # Agent tools (data access, RAG, retry logic)
├── rag/                  # ChromaDB embedder + retriever
├── data/                 # SQLite logs
├── exports/              # Gold layer CSVs from Databricks
├── api.py                # FastAPI backend
├── app.py                # Streamlit frontend
├── Dockerfile / docker-compose.yml
└── requirements.txt
\`\`\`

## Setup

1. \`pip install -r requirements.txt\`
2. Add \`GROQ_API_KEY\` to \`.env\`
3. Place Gold layer CSVs in \`exports/\`
4. Build RAG vector store: \`python rag/embedder.py\`
5. Run backend: \`python api.py\`
6. Run frontend: \`streamlit run app.py\`

## Key Features

- **Medallion Architecture** on Databricks (Bronze/Silver/Gold)
- **5 specialized AI agents** coordinated by an Orchestrator
- **RAG-powered chatbot** for natural language queries over financial data
- **Automatic retry logic** with rate-limit-aware backoff
- **Model routing** — lightweight tasks use Llama 3.1 8B, complex reasoning uses Llama 3.3 70B
- **Activity logging** for agent run history and token usage tracking