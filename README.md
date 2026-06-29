# Investment Management Engine Core Spine

An asynchronous wealth management microservice built with **FastAPI** and **Python 3.11+**. The system processes user investment queries through a deterministic safety validation pipeline, classifies intent, and streams real-time portfolio metrics using Server-Sent Events (SSE).

This project was built out completely in a test-driven development environment to establish a robust execution skeleton before rolling out live model connections.

---

## 🛠️ System Architecture & Workflow

Every client request follows a strict, sequential pipeline to minimize cost, guarantee low-latency safety boundaries, and prevent user-side loading delays:

```text
                                [User Request] 
                                      │
                                      ▼
1. Safety Guard (Local / Sync)  ──[Blocked]──> [SSE: safety_block] ──> [Close Channel]
                                      │
                                   [Passed]
                                      ▼
2. Intent Classifier (Dev Heuristics) ───────> [SSE: classification]
                                      │
                                      ▼
3. Agent Router 
      ├── Mapped to 'portfolio_health' ──────> [SSE: agent_response] ──> [Done]
      └── Mapped to other intent tags ───────> [SSE: agent_stub] ─────> [Done]

```
---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AamirRaza01/investment-management-engine.git
cd working dir
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

**Run Tests**

```bash
pytest tests/ -v
```

**Start Development Server**

```bash
uvicorn src.main:app --reload --port 8000
```

**Test Streaming Pipeline**

```bash
python -c "import httpx; r = httpx.post('http://127.0.0.1:8000/api/chat', json={'query': 'How is my portfolio doing?', 'user_id': 'usr_003', 'prior_user_turns': []}, timeout=10.0); print(r.text)"
```
---

### 🔮 Future Production Advancements

1. Migrate from static JSON profiles to a hosted relational database for dynamic user portfolio tracking.
2. Transition keyword routing heuristics into live model reasoning utilizing structured JSON SDK parsing capabilities.
3. Integrate live financial stock data providers to replace placeholder telemetry metrics with real-time calculations.
