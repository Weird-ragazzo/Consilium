# Consilium

**A council of AI models deliberates on your question.**

Consilium now uses a Groq-backed, safety-first medical deliberation pipeline. It extracts relevant clinical facts, routes requests by risk, runs two independent analysts, verifies claims against retrieved evidence, and returns a structured answer instead of raw model output.

---

## How It Works

```
User Question
     │
     ▼
┌──────────────────────────────────────────┐
│  Phase 1 · GENERATE                      │
│  Both models answer independently        │
│  (parallel)                              │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Phase 2 · CRITIQUE                      │
│  Each model critiques the other's        │
│  response for errors, gaps, reasoning    │
│  (parallel, cross-review)                │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Phase 3 · REVISE                        │
│  Each model revises its own answer       │
│  based on the critique it received       │
│  (parallel)                              │
└──────────────┬───────────────────────────┘
               │
               ▼
       Final Responses
    (side-by-side comparison)
```

## Models

| Role    | Model                        | Provider |
|---------|------------------------------|----------|
| Router  | `openai/gpt-oss-20b`         | Groq |
| Safety  | `openai/gpt-oss-safeguard-20b` | Groq |
| Analyst | `openai/gpt-oss-120b` / `openai/gpt-oss-20b` | Groq |
| Evidence / final adjudication | `openai/gpt-oss-120b` | Groq |

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3.12, FastAPI, Uvicorn       |
| Frontend | React 19, TypeScript, Vite          |
| LLM API  | Groq SDK (OpenAI-compatible API)    |
| Styling  | Custom CSS, Framer Motion           |
| Fonts    | Instrument Serif, Sora (Google)     |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- One Groq API key

### 1. Clone & set up environment

```bash
git clone <repo-url>
cd Consilium

# Python
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` with your Groq API key and optional model overrides:

```env
GROQ_API_KEY=your_key_here
MODEL_ROUTER=openai/gpt-oss-20b
MODEL_SAFETY=openai/gpt-oss-safeguard-20b
MODEL_SIMPLE=openai/gpt-oss-20b
MODEL_MODEL1=openai/gpt-oss-120b
MODEL_MODEL2=openai/gpt-oss-20b
MODEL_MODEL3=openai/gpt-oss-120b
MODEL_VISION=qwen/qwen3.6-27b
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Project Structure

```
Consilium/
├── .env.example             # Template for API keys
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings & environment variables
│   ├── llm_client.py        # Async Groq client wrapper with retries and JSON helpers
│   ├── models.py            # Pydantic request/response schemas
│   ├── pipeline.py          # 3-phase deliberation pipeline
│   ├── prompts.py           # System prompts & templates
│   ├── requirements.txt     # Python dependencies
│   └── routers/
│       └── council.py       # POST /api/council endpoint
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts        # Dev server & API proxy
    └── src/
        ├── App.tsx           # Root component
        ├── App.css           # All component styles
        ├── index.css         # Global theme & variables
        ├── api/
        │   └── council.ts    # API client
        ├── components/
        │   ├── CouncilView.tsx
        │   ├── PhaseIndicator.tsx
        │   ├── PromptInput.tsx
        │   └── ResponsePanel.tsx
        └── types/
            └── index.ts      # TypeScript interfaces
```

## API

### `POST /api/council`

**Request:**
```json
{
  "prompt": "Is nuclear energy safe?"
}
```

**Response:**
```json
{
  "prompt": "Is nuclear energy safe?",
  "route": "MEDICAL_ANALYSIS",
  "safety": {
    "risk_level": "safe",
    "route_override": false,
    "red_flags": [],
    "reason": "..."
  },
  "answer": "...",
  "assessment": {
    "certainty": "possible",
    "evidence_quality": "moderate"
  },
  "extracted_information": {
    "symptoms": [],
    "duration": null,
    "severity": null,
    "age": null,
    "sex": null,
    "report_values": [],
    "medications": [],
    "history": [],
    "missing_information": [],
    "ambiguous_information": [],
    "unreadable_information": []
  },
  "claims": [],
  "sources": [],
  "uncertainties": [],
  "model_details": null,
  "final_safety": null,
  "phases_completed": ["safety_and_routing", "information_extraction", "dual_model_analysis", "evidence_retrieval", "peer_review", "re_evaluation", "final_claim_matrix", "final_adjudication", "final_safety_gate"]
}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## Configuration

All settings are managed via environment variables (loaded from `.env`):

| Variable               | Default                                  | Description              |
|------------------------|------------------------------------------|--------------------------|
| `GROQ_API_KEY`          | —                                        | Groq API key             |
| `MODEL_ROUTER`          | `openai/gpt-oss-20b`                      | Router model             |
| `MODEL_SAFETY`          | `openai/gpt-oss-safeguard-20b`            | Safety classifier        |
| `MODEL_SIMPLE`          | `openai/gpt-oss-20b`                      | Simple/general answers   |
| `MODEL_MODEL1`          | `openai/gpt-oss-120b`                     | Clinical analyst         |
| `MODEL_MODEL2`          | `openai/gpt-oss-20b`                      | Skeptical analyst        |
| `MODEL_MODEL3`          | `openai/gpt-oss-120b`                     | Evidence adjudicator     |
| `MODEL_VISION`          | `qwen/qwen3.6-27b`                        | Future vision/report use |
| `MAX_TOKENS`            | `2048`                                   | Max tokens per LLM call  |
| `TEMPERATURE`           | `0.3`                                    | Sampling temperature     |

---

## License

Private project — all rights reserved.
