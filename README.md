# Nifty Insights — Agentic Financial Intelligence Platform

A multi-agent AI system for processing, analyzing, and querying 28 years of Nifty 50 stock market data (1998–2026). Built on a Databricks Medallion architecture, five specialized AI agents, retrieval-augmented generation, and a live data feed — wrapped in a custom React interface.

**Live demo:** https://financial-insights-project-i5b4-km525kmis.vercel.app · **API:** Render

---

## Overview

This project automates the full lifecycle of financial data analysis — ingestion, cleaning, statistical analysis, and natural-language Q&A — using a coordinated team of AI agents rather than a single monolithic script. It was built to explore how agentic AI systems behave under real-world constraints: rate limits, multi-provider model routing, RAG retrieval quality, and production deployment.

```
Raw Nifty 50 Data (Kaggle, 1998–2026)
        ↓
Databricks · PySpark
Bronze → Silver → Gold  (Medallion Architecture, Delta Lake)
        ↓
┌─────────────────────────────────────────────┐
│              AI Agent Layer (ADK)             │
│                                                │
│  Orchestrator Agent                           │
│   ├── Ingestion Agent                         │
│   ├── Processing Agent                        │
│   └── Analytics Agent                         │
│                                                │
│  Chatbot Agent (RAG)                          │
│   ├── ChromaDB Vector Store                   │
│   └── Live Snapshot Tool (yfinance)           │
└─────────────────────────────────────────────┘
        ↓
FastAPI Backend  →  React Frontend (Chat · Dashboard · Admin)
```

---

## Features

- **Medallion data pipeline** on Databricks — raw CSV → cleaned, enriched, anomaly-flagged data → aggregated analytics tables
- **Five coordinated AI agents** (Ingestion, Processing, Analytics, Orchestrator, Chatbot), each scoped to a single responsibility
- **RAG-powered chatbot** over real historical statistics — every figure cited is sourced from the dataset, not generated freehand
- **Bounded conversation memory** — the chatbot understands follow-up questions ("I don't like that, suggest something else") without unbounded context growth
- **Live data refresh** — pulls current trading-day prices via `yfinance`, separate from the historical archive, so the chatbot can answer "how is X doing today/recently"
- **Cost-aware model routing** — lighter agents run on smaller/cheaper models, complex reasoning routed to more capable ones, balanced against free-tier rate limits across two providers (Groq, Google Gemini)
- **Resilient by design** — automatic retry with backoff on rate limits, sanitization of malformed model output, graceful fallbacks rather than hard failures
- **Custom UI** — a from-scratch React frontend (not a generic dashboard template), with a public chat + dashboard experience and a separately authenticated admin panel
- **Configurable dashboard** — sector comparisons, top/worst performers, and per-ticker trend charts, all driven by user-selected filters rather than fixed views

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data engineering | Databricks, PySpark, Delta Lake |
| AI agents | Google Agent Development Kit (ADK) |
| LLM providers | Google Gemini, Groq (Llama models) |
| RAG | ChromaDB, ONNX MiniLM embeddings |
| Live data | yfinance |
| Backend | FastAPI |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Storage | SQLite (activity/usage logging) |
| Deployment | Render (API), Vercel (frontend) |

---

## Project Structure

```
financial-insights-project/
├── agents/                  # 5 AI agents (ingestion, processing, analytics, orchestrator, chatbot)
├── tools/                   # Agent tools — data access, RAG retrieval, retry logic, SQLite logging
├── rag/                     # ChromaDB embedder + retriever
├── data/                    # SQLite activity logs
├── exports/                 # Gold-layer CSVs (from Databricks) + live snapshot data
├── api.py                   # FastAPI backend — chat, pipeline, dashboard, and admin endpoints
├── daily_refresh.py         # yfinance live data fetcher
├── requirements.txt
├── financial-insights-ui/   # React frontend
│   ├── src/
│   │   ├── pages/           # Chat, Dashboard, Admin
│   │   ├── components/      # Layout, TickerTape, Controls
│   │   └── lib/             # API client
│   └── vercel.json          # SPA routing config
└── README.md
```

---

## Architecture Notes

### Why five agents instead of one script?

Each agent owns a single responsibility — ingestion validation, statistical processing, report generation, orchestration, or conversational Q&A — so each can be tested, retried, and reasoned about independently. The Orchestrator coordinates the other three for end-to-end pipeline runs; the Chatbot operates independently for on-demand queries.

### Why two LLM providers?

Different providers' free tiers impose different constraints (requests/minute, tokens/day). Routing agents across Gemini and Groq — and across model sizes within Groq — was a deliberate response to those constraints, not an accident: lighter, more frequent calls (ingestion checks, casual chat) use cheaper/faster models; heavier reasoning (multi-section reports, multi-step orchestration) uses more capable ones. This required handling provider-specific quirks (e.g., a known compatibility issue between certain reasoning-model outputs and multi-turn tool-calling, which was resolved by routing the Orchestrator to a provider without that issue).

### Why a separate "live snapshot" rather than rebuilding the historical dataset daily?

The historical Gold-layer tables represent a fixed, validated 1998–2026 archive. Live data is fetched into a separate file and exposed through its own tool, so the chatbot can distinguish "yearly historical average" from "yesterday's actual close" — these are genuinely different questions with different correct answers, and conflating them was an early bug this design fixes.

### Known constraint: free-tier rate limits

This project intentionally runs entirely on free-tier API access. That means occasional rate-limit waits during heavy testing are expected, not a defect — the retry/backoff logic, model routing, and graceful degradation throughout the system exist specifically to make that constraint usable rather than to pretend it doesn't exist.

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Groq API key and/or Google AI Studio API key
- Databricks workspace (only needed if rebuilding the Gold-layer data from scratch)

### Backend

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
ADMIN_API_KEY=choose_a_secret_string
```

Build the RAG vector store (one-time):
```bash
python rag/embedder.py
```

Run the API:
```bash
python api.py
```

### Frontend

```bash
cd financial-insights-ui
npm install
cp .env.example .env   # set VITE_API_BASE to your API URL
npm run dev
```

---

## Deployment

- **Backend** → Render (Docker-based web service). Set `GROQ_API_KEY`, `GOOGLE_API_KEY`, and `ADMIN_API_KEY` as environment variables in the Render dashboard.
- **Frontend** → Vercel. Set the project's root directory to `financial-insights-ui`, framework preset to Vite, and `VITE_API_BASE` to your deployed Render URL. A `vercel.json` rewrite rule is included to support client-side routing.

---

## Data Source

Historical data: Nifty 50 historical dataset (Kaggle), covering 49 constituent stocks across 13 sectors, 1998–2026. Live data: fetched on demand via `yfinance` (Yahoo Finance).

---

## Disclaimer

This project is for educational and demonstrative purposes. All chatbot responses are grounded in historical or near-real-time market data, but nothing in this application constitutes financial advice. Consult a licensed financial advisor before making investment decisions.
