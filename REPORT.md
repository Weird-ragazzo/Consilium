# Consilium — Project Report (v1.0)

**Author:** Dhruv Raghav  
**Date:** February 18, 2026  
**Version:** 1.0.0  

---

## 1. Executive Summary

Consilium is a web application that implements a **multi-model deliberation pipeline** — a structured process where two large language models independently answer a user's question, cross-critique each other's responses, and then revise their answers based on the feedback received. The goal is to produce higher-quality, peer-reviewed AI responses by leveraging adversarial collaboration between models.

The name *Consilium* (Latin: "council, deliberation") reflects the core concept — convening a council of AI minds to deliberate before delivering a final answer.

---

## 2. Problem Statement

Single-model LLM responses often suffer from:

- **Unchecked errors** — factual mistakes go unnoticed without review
- **Blind spots** — a single model may miss important perspectives or nuances
- **Overconfidence** — models rarely self-critique effectively
- **Inconsistency** — quality varies significantly across prompts

Consilium addresses these by introducing structured peer review between models, forcing each to defend or improve its reasoning under critique.

---

## 3. Architecture

### 3.1 System Architecture

```
┌─────────────────┐       HTTP        ┌─────────────────────┐
│                 │   POST /api/      │                     │
│   React/Vite    │ ──────────────▶   │   FastAPI Backend   │
│   Frontend      │                   │                     │
│   (port 5173)   │ ◀──────────────   │   (port 8000)       │
│                 │    JSON Response   │                     │
└─────────────────┘                   └────────┬────────────┘
                                               │
                                     ┌─────────▼─────────┐
                                     │  NVIDIA NIM API    │
                                     │  (OpenAI-compat)   │
                                     │                    │
                                     │  • Llama 4 Scout   │
                                     │  • Llama 3.1 8B    │
                                     └────────────────────┘
```

### 3.2 Deliberation Pipeline

The core pipeline executes three sequential phases, with parallel model calls within each phase:

| Phase | Action | Model A | Model B |
|-------|--------|---------|---------|
| **1. Generate** | Both models answer the question independently | Llama 4 Scout answers | Llama 3.1 8B answers |
| **2. Critique** | Each model critiques the *other's* response | A critiques B's answer | B critiques A's answer |
| **3. Revise** | Each model revises its *own* answer using the critique it received | A revises using B's critique | B revises using A's critique |

All phases use `asyncio.gather()` for parallel execution, minimizing total latency.

### 3.3 Prompt Engineering

Four distinct system prompts govern model behavior:

- **SYSTEM_PROMPT_GENERATE** — Instructs the model to be a helpful, thorough assistant
- **SYSTEM_PROMPT_CRITIQUE** — Instructs the model to act as a critical reviewer, following a Strengths / Weaknesses / Suggestions structure
- **CRITIQUE_USER_TEMPLATE** — Formats the original question + response being critiqued
- **SYSTEM_PROMPT_REVISE** — Instructs the model to consider the critique and revise if warranted, or explain why no revision is needed
- **REVISE_USER_TEMPLATE** — Formats the original question + own response + critique received

---

## 4. Technical Implementation

### 4.1 Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI 0.115 | Async REST API server |
| Server | Uvicorn 0.30 | ASGI server with hot-reload |
| LLM SDK | OpenAI Python SDK 1.50 | NVIDIA NIM API client (OpenAI-compatible) |
| Config | Pydantic Settings 2.5 | Type-safe environment configuration |
| HTTP | httpx 0.27 | Async HTTP transport (pinned for compatibility) |

**Key files:**

| File | Responsibility |
|------|-------------|
| `main.py` | App initialization, CORS, router mounting |
| `config.py` | Environment variables & default model configuration |
| `llm_client.py` | Async wrapper around OpenAI SDK with `<think>` block stripping |
| `pipeline.py` | Three-phase deliberation orchestration |
| `prompts.py` | All system prompts and user message templates |
| `models.py` | Pydantic schemas for request/response validation |
| `routers/council.py` | Single POST endpoint at `/api/council` |

### 4.2 Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React 19 | UI component library |
| Language | TypeScript 5.9 | Type-safe development |
| Build | Vite 6.4 | Dev server with API proxy & HMR |
| Animation | Framer Motion 12 | Entrance animations & accordion transitions |
| Fonts | Instrument Serif + Sora | Editorial typography via Google Fonts |

**Key components:**

| Component | Responsibility |
|-----------|-------------|
| `App.tsx` | Root layout, phase state management, error handling |
| `PromptInput.tsx` | Textarea form with Ctrl+Enter shortcut, gold gradient submit button |
| `PhaseIndicator.tsx` | Three-step progress stepper with Roman numerals (I, II, III) |
| `CouncilView.tsx` | Grid layout with staggered reveal animations |
| `ResponsePanel.tsx` | Model answer card with expandable deliberation details |

### 4.3 API Contract

**Endpoint:** `POST /api/council`

```
Request  → { prompt: string }
Response → {
  prompt: string,
  model_a: ModelResponse,
  model_b: ModelResponse,
  phases_completed: string[]
}

ModelResponse → {
  model_name: string,
  model_id: string,
  initial_response: string,
  critique_received: string,
  final_response: string,
  was_revised: boolean
}
```

The `was_revised` flag is computed server-side by comparing `initial_response` against `final_response` (stripped whitespace comparison).

---

## 5. Design

### 5.1 Aesthetic Direction

**Neo-Classical Editorial** — warm gold on deep obsidian, inspired by luxury editorial print design.

| Element | Choice |
|---------|--------|
| Background | Deep obsidian `#08080c` with SVG grain overlay |
| Accent | Warm gold `#c8a44e` with copper secondary `#a87d5e` |
| Display Font | Instrument Serif (italic) — distinctive serif with character |
| Body Font | Sora — geometric sans-serif for readability |
| Layout | Centered 920px max-width, generous vertical rhythm |
| Interaction | Framer Motion entrance reveals, pulse animations on active phase |

### 5.2 UI Features

- **Header** — Italic serif title with diamond ornament and gradient divider
- **Input** — Serif italic placeholder, gold-gradient CTA button with arrow animation
- **Phase Stepper** — Horizontal three-step timeline with Roman numerals, pulsing ring on active step, checkmarks on complete
- **Response Cards** — Top accent line, serif model names, pill badges (Revised/Unchanged), animated accordion for deliberation details
- **Error States** — Contextual error banners with icon and stepper error indication

---

## 6. Models Used

### Llama 4 Scout 17B (Model A)

- **Full ID:** `meta/llama-4-scout-17b-16e-instruct`
- **Parameters:** 17B active (16 experts, mixture-of-experts)
- **Role:** Primary responder — larger model with stronger reasoning
- **Provider:** NVIDIA NIM API

### Llama 3.1 8B Instruct (Model B)

- **Full ID:** `meta/llama-3.1-8b-instruct`
- **Parameters:** 8B
- **Role:** Secondary responder & cross-reviewer — smaller but fast
- **Provider:** NVIDIA NIM API

The deliberate asymmetry (17B vs 8B) is intentional — it tests whether a smaller model's critique can meaningfully improve a larger model's response, and vice versa.

---

## 7. Setup & Deployment

### Requirements

- Python 3.12+
- Node.js 18+
- Two NVIDIA NIM API keys

### Running

```bash
# Backend (from project root)
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

Application runs at `http://localhost:5173` with API proxy to port 8000.

---

## 8. Known Limitations (v1.0)

1. **Single blocking request** — the API call blocks for 20-40 seconds while all three phases complete; no streaming or SSE
2. **No conversation history** — each request is stateless; there is no follow-up capability
3. **Phase timing is simulated** — the frontend phase stepper uses `setTimeout` heuristics, not real server progress updates
4. **Two models only** — the pipeline is hardcoded for exactly two participants
5. **No caching** — identical prompts re-execute the full pipeline every time
6. **No authentication** — the API is open, suitable for local use only

---

## 9. Future Work (v2.0 Candidates)

- **Server-Sent Events (SSE)** for real-time phase progress from the backend
- **Streaming responses** to display tokens as they arrive
- **Configurable model selection** via the frontend UI
- **N-model council** — extend beyond two participants
- **Conversation memory** — multi-turn deliberation
- **Response quality scoring** — automated evaluation of improvement after revision
- **Export/share** — save or share deliberation results
- **Dark/light theme toggle**

---

## 10. Conclusion

Consilium v1.0 demonstrates that structured inter-model deliberation — Generate, Critique, Revise — can be implemented as a lightweight, self-contained web application. The pipeline's cross-review mechanism forces models to confront each other's blind spots, consistently producing revised answers that are more thorough and balanced than their initial responses. The asymmetric model pairing (Llama 4 Scout 17B + Llama 3.1 8B) validates that even smaller models can provide valuable critical feedback to larger ones.
