# Consilium — Project Report (v1.0)

**Author:** Dhruv Raghav  
**Date:** February 18, 2026  
**Version:** 1.0.0  

---

## 1. Executive Summary

Consilium is a web application that implements a **multi-model deliberation pipeline** — a structured process where two large language models independently answer a user's question, cross-critique each other's responses, and then revise their answers based on the feedback received. The current implementation has been migrated to Groq and expanded into a medical information / decision-support workflow with safety routing, relevant-information extraction, claim-evidence verification, peer review, re-evaluation, and final adjudication.

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
                                     │      GroqCloud     │
                                     │ (OpenAI-compatible)│
                                     │                    │
                                     │  • GPT-OSS models  │
                                     │  • Safety / Vision │
                                     └────────────────────┘
```

### 3.2 Deliberation Pipeline

The core pipeline now executes multiple safety-first phases, with parallel model calls where calls are independent:

| Phase | Action | Notes |
|-------|--------|-------|
| **1. Safety & Routing** | Safety classifier and router run in parallel | Safety can override routing |
| **2. Relevant Extraction** | Clinical facts are extracted from the user's prompt | No forced complete patient profile |
| **3. Generate** | Two analysts answer independently | GPT-OSS 120B + GPT-OSS 20B |
| **4. Evidence Retrieval** | Claims are extracted and checked against browser-search evidence | Browser search is separate from structured JSON |
| **5. Critique** | Each model critiques the other's initial analysis | Independent cross-review |
| **6. Revise** | Each model revises its own answer based on critique | Disagreement is allowed |
| **7. Adjudicate** | Model 3 synthesizes the verified record | Evidence-first final synthesis |
| **8. Final Safety Gate** | Last audit for emergency / unsafe output | Emergency guidance is elevated |

All phases use `asyncio.gather()` for parallel execution, minimizing total latency.

### 3.3 Prompt Engineering

The system now uses the following prompt layers:

- **SAFETY_SYSTEM_PROMPT** — Detects urgent/emergency medical situations and unsafe requests
- **ROUTER_SYSTEM_PROMPT** — Routes requests into simple, general, medical analysis, urgent, or emergency paths
- **EXTRACTION_SYSTEM_PROMPT** — Extracts only the relevant provided clinical facts and flags missing/ambiguous/unreadable information
- **MODEL_1 / MODEL_2 prompts** — Independent clinical analyst and skeptical analyst roles
- **CLAIM_EXTRACTION / CLAIM_EVALUATION prompts** — Build the claim-evidence matrix from model output and browser-search evidence
- **MODEL_3 prompt** — Final evidence-first adjudication
- **FINAL_SAFETY_PROMPT** — Last audit for unsafe or emergency output

---

## 4. Technical Implementation

### 4.1 Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI 0.115 | Async REST API server |
| Server | Uvicorn 0.30 | ASGI server with hot-reload |
| LLM SDK | Groq Python SDK | Groq API client (OpenAI-compatible) |
| Config | Pydantic Settings 2.5 | Type-safe environment configuration |
| HTTP | httpx 0.27 | Async HTTP transport (pinned for compatibility) |

**Key files:**

| File | Responsibility |
|------|-------------|
| `main.py` | App initialization, CORS, router mounting |
| `config.py` | Environment variables & default model configuration |
| `llm_client.py` | Async Groq wrapper with retries, JSON helpers, and browser-search support |
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
  route: string,
  safety: SafetyClassification,
  answer: string,
  assessment: { certainty: string, evidence_quality: string },
  extracted_information: ExtractedInformation,
  claims: ClaimMatrixEntry[],
  sources: Source[],
  uncertainties: UncertaintyItem[],
  model_details: Record<string, ModelDeliberationDetail> | null,
  final_safety: FinalSafetyCheck | null,
  phases_completed: string[]
}
```

Each `model_details.*.was_revised` flag is computed server-side by comparing the model’s initial analysis against its revised analysis after peer review and evidence verification.

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

### Model Roles

- **Router** — `openai/gpt-oss-20b`
- **Safety classifier** — `openai/gpt-oss-safeguard-20b`
- **Clinical analyst** — `openai/gpt-oss-120b`
- **Skeptical analyst** — `openai/gpt-oss-20b`
- **Evidence adjudicator** — `openai/gpt-oss-120b`
- **Vision / report parsing** — `qwen/qwen3.6-27b`

The asymmetric pairing between the analyst models is intentional — the stronger model looks for broad clinical possibilities while the smaller model is used as a skeptical counterweight.

---

## 7. Setup & Deployment

### Requirements

- Python 3.12+
- Node.js 18+
- One Groq API key

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

1. **Single blocking request** — the API call blocks while all phases complete; no streaming or SSE yet
2. **No conversation history** — each request is stateless; there is no follow-up capability
3. **Phase timing is simulated** — the frontend phase stepper uses `setTimeout` heuristics, not real server progress updates
4. **No OCR/upload path yet** — the future image/report flow is scaffolded conceptually but not wired into the UI
5. **No caching** — identical prompts re-execute the full pipeline every time
6. **No authentication** — the API is open, suitable for local use only

---

## 9. Future Work (v2.0 Candidates)

- **Server-Sent Events (SSE)** for real-time phase progress from the backend
- **Streaming responses** to display tokens as they arrive
- **Image/PDF upload path** for report parsing and OCR with the vision model
- **Configurable model selection** via the frontend UI
- **N-model council** — extend beyond two participants
- **Conversation memory** — multi-turn deliberation
- **Response quality scoring** — automated evaluation of improvement after revision
- **Export/share** — save or share deliberation results
- **Dark/light theme toggle**

---

## 10. Conclusion

Consilium v1.0 demonstrates that structured inter-model deliberation — now extended into a Groq-backed medical evidence workflow — can be implemented as a lightweight, self-contained web application. The pipeline's cross-review mechanism forces models to confront each other's blind spots, while the claim-evidence layer and final safety gate keep the output constrained to verifiable, medically cautious guidance.
