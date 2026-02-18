# Consilium

**A council of AI models deliberates on your question.**

Consilium pits two LLMs against each other in a structured three-phase deliberation pipeline — Generate, Critique, Revise — to produce higher-quality, peer-reviewed answers to any question.

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

| Role    | Model                                | Provider       |
|---------|--------------------------------------|----------------|
| Model A | `meta/llama-4-scout-17b-16e-instruct` | NVIDIA NIM API |
| Model B | `meta/llama-3.1-8b-instruct`          | NVIDIA NIM API |

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3.12, FastAPI, Uvicorn       |
| Frontend | React 19, TypeScript, Vite          |
| LLM API  | NVIDIA NIM (OpenAI-compatible SDK)  |
| Styling  | Custom CSS, Framer Motion           |
| Fonts    | Instrument Serif, Sora (Google)     |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Two NVIDIA NIM API keys (free tier available at [build.nvidia.com](https://build.nvidia.com))

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

Edit `.env` with your NVIDIA API keys:

```env
NVIDIA_API_KEY_LLAMA=nvapi-your-first-key
NVIDIA_API_KEY_LLAMA2=nvapi-your-second-key
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
│   ├── llm_client.py        # Async OpenAI-compatible LLM client
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
  "model_a": {
    "model_name": "Llama 4 Scout",
    "model_id": "meta/llama-4-scout-17b-16e-instruct",
    "initial_response": "...",
    "critique_received": "...",
    "final_response": "...",
    "was_revised": true
  },
  "model_b": {
    "model_name": "Llama 3.1 8B",
    "model_id": "meta/llama-3.1-8b-instruct",
    "initial_response": "...",
    "critique_received": "...",
    "final_response": "...",
    "was_revised": true
  },
  "phases_completed": ["generate", "critique", "revise"]
}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## Configuration

All settings are managed via environment variables (loaded from `.env`):

| Variable               | Default                                  | Description              |
|------------------------|------------------------------------------|--------------------------|
| `NVIDIA_API_KEY_LLAMA`  | —                                        | API key for Model A      |
| `NVIDIA_API_KEY_LLAMA2` | —                                        | API key for Model B      |
| `NVIDIA_BASE_URL`       | `https://integrate.api.nvidia.com/v1`    | NIM API endpoint         |
| `MODEL_A`               | `meta/llama-4-scout-17b-16e-instruct`    | Model A identifier       |
| `MODEL_B`               | `meta/llama-3.1-8b-instruct`             | Model B identifier       |
| `MAX_TOKENS`            | `1024`                                   | Max tokens per LLM call  |
| `TEMPERATURE`           | `0.7`                                    | Sampling temperature     |

---

## License

Private project — all rights reserved.
