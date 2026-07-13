# Finlatics: Multi-Agent Investment Management Engine

An asynchronous wealth management microservice built with **FastAPI**, **LangGraph**, and **Python 3.11+**. The system orchestrates an ecosystem of autonomous specialized agents to deliver live portfolio analytics, market news sentiment, and tax strategies over a real-time streaming channel.

This project implements a hybrid deterministic and probabilistic runtime architecture, providing ultra-low latency validation checks alongside complex, state-aware LLM reasoning loops.

---

## 🛠️ System Architecture & Workflow

Every client request passes through a stateful graph topology designed to ensure hard compliance isolation, maintain multi-turn context, and prevent data-blocking delays:

```text
                                            [ Incoming User Request ]
                                   (JSON Payload: query, user_id, session_id)
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │    1. Local Safety Guard  │──[Blocked]──> [SSE: safety_block] ──> [Close Channel]
                                         │ (Deterministic Heuristics)│                    (Returns Compliance Message)
                                         └───────────────────────────┘
                                                       │
                                                   [Passed]
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ 2. LangGraph Router Node  │─────── [SSE: classification] 
                                         └───────────────────────────┘   (Emits extracted Intent & Tickers)
                                           /           │           \
                              [portfolio_health]  [market_news]   [tax_strategy]
                                  /                    │                    \
                                 ▼                     ▼                     ▼
                          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
                          │ Health Agent │      │  News Agent  │      │  Tax Agent   │
                          └──────────────┘      └──────────────┘      └──────────────┘
                                 │                     │                     │
                            [Triggers DB]       [Triggers API]         [Triggers Core]
                                 │                     │                     │
                                 ▼                     ▼                     ▼
                          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
                          │SQLAlchemy ORM│      │yfinance API  │      │ Static Rule  │
                          │PostgreSQL engine    │Live metrics  │      │ Multi-period │
                          │Fetch assets  │      │Ticker news   │      │ Allocations  │
                          └──────────────┘      └──────────────┘      └──────────────┘
                                 │                     │                     │
                                 ▼                     ▼                     ▼
                          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
                          │Compute Net   │      │Extract News  │      │ Evaluate     │
                          │Valuation &   │      │Sentiment &   │      │ Gains        │
                          │Concentration │      │Headlines     │      │ Harvesting   │
                          └──────────────┘      └──────────────┘      └──────────────┘
                                 \                     │                     /
                            [Emit Agent Payload] [Emit Agent Payload] [Emit Agent Payload]
                                  \                    │                    /
                                   ▼                   ▼                   ▼
                                ┌─────────────────────────────────────────┐
                                │         3. Response Synthesizer Node    │
                                │        (Aggregates Multi-Agent Data)    │
                                └─────────────────────────────────────────┘
                                                       │
                                                       ▼
                                          [SSE: final_insight chunk]
                                         (Human-friendly markdown text)
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ 4. Thread Memory Node     │──> [MemorySaver Cache Thread Persistence]
                                         │ (State Update Mechanics)  │──> [SSE: done] ──> [Close Channel Connection]
                                         └───────────────────────────┘

```

## 🔄 Complete End-to-End Execution Breakdown

### 1. User Request Initialization
Client posts a raw JSON transaction block specifying:

- User metadata credentials (`user_id`)
- Thread constraints (`session_id`)
- Natural language query

This request is sent to the server payload engine for processing.

---

### 2. Deterministic Safety Guard

A high-speed, localized token-matching guard layer evaluates incoming requests in under **10ms**.

If patterns indicate intent to perform:

- Insider trading
- Market manipulation
- Fraud

the graph execution terminates immediately before invoking any expensive LLM resources.

---

### 3. Probabilistic Intent Routing Node

Uses **Groq (Llama-3.3-70B)** to perform intelligent runtime evaluation.

Responsibilities include:

- Intent classification
- Financial ticker extraction (e.g. `NVDA`, `AAPL`)
- Context history sanitization
- Dynamic graph routing through conditional state edges

---

### 4. Specialized Computing Agent Network

#### 📊 Portfolio Health Agent (SQL Injection Protection)

- Creates an active database session using SQLAlchemy ORM
- Fetches user portfolio allocations from PostgreSQL
- Cross-references holdings against live market prices
- Computes:
  - Portfolio valuation
  - Risk metrics
  - Stock concentration warnings

---

#### 📰 Market News Agent (Live Network I/O)

- Executes asynchronous Finance API calls
- Retrieves live ticker feeds
- Extracts financial headlines
- Generates market sentiment consensus

---

#### 💰 Tax Strategy Agent (Scale Stub Framework)

Evaluates investment timelines to compute capital gains optimization strategies using structural taxation rules.

---

### 5. Conversational Synthesizer Node

Aggregates outputs from all specialized agents and:

- Removes machine-generated formatting noise
- Merges metrics
- Produces a professional wealth management response

---

### 6. Thread-Level Asynchronous Memory Layer

Persists conversation state using the native **LangGraph MemorySaver** checkpointer.

Before closing the request it:

- Stores thread state
- Emits Server-Sent Events (SSE)
- Streams response chunks asynchronously
- Terminates connection gracefully

---

# 🚀 Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/investment-management-engine.git

cd investment-management-engine
```

---

## 2. Create a Virtual Environment & Install Dependencies

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
.\venv\Scripts\activate

pip install -r requirements.txt
```

---

## 3. Configure Environment Constants

Create a `.env` file in the project root.

```env
GROQ_API_KEY="your_groq_api_key_here"

DATABASE_URL="postgresql://username:password@localhost:5432/valura_db"
```

---

# 🧪 Testing & Execution

## Run Operational Tests

```bash
pytest tests/ -v
```

---

## Start Live Production Server

```bash
uvicorn src.main:app --reload --port 8000
```

---

## Test Multi-Turn Streaming Pipeline

Fire a mock query stream directly using **httpx** from another terminal to observe non-blocking Server-Sent Events (SSE) processing.

```bash
python -c "
import httpx

r = httpx.post(
    'http://127.0.0.1:8000/api/chat',
    json={
        'user_id':'demo',
        'session_id':'thread-001',
        'query':'Analyze my Apple portfolio.'
    }
)

print(r.text)
"
```
