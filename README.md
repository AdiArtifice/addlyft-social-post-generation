# AddLyft — Social Post Generation

R&D showcase that turns a short ad brief into a **ready-to-review social post**:
structured caption / offer / CTA / hashtags **plus** an optional portrait poster
image (0–3 reference uploads).

This repo is the **social-post deliverable only**. Ad video / Veo work is not
included.

| | |
|---|---|
| Primary UI | http://127.0.0.1:5173/ |
| Backend API | http://127.0.0.1:8000 |
| Text model | `gemini-2.5-flash-lite` (Vertex AI) |
| Image model | `gemini-3.1-flash-lite-image` (9:16, 1K) |
| Demo store | Fixed **AMPM Woodstock** (stands in for a prior store-select step) |

Outputs are **AI drafts** — nothing is published to social platforms.

## Repo layout

```
backend/                 # FastAPI: /api/generate + /api/generate-image
frontend/                # React (Vite) showcase UI
social-post-image/       # Image engine (prompts, Vertex client); optional :8787 UI
reports/                 # Social-post audit / token reports (PDF + generators)
references/              # Sample reference images for demos
usage.py                 # Text token cost estimator + logger
```

## Prerequisites

1. Python 3.11+ with a local venv at repo root (`.venv/`)
2. Node.js 18+ for the frontend
3. Google Cloud project with Vertex AI enabled
4. Application Default Credentials: `gcloud auth application-default login`
5. Root `.env` (not committed) — see below

## Setup

```powershell
# From repo root
python -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements.txt
# Also install image deps used by social-post-image (Pillow, etc.) if not already present

cd frontend
npm install
cd ..
```

### `.env` (repo root, do not commit)

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash-lite

IMAGE_MODEL=gemini-3.1-flash-lite-image
IMAGE_LOCATION=global
IMAGE_ASPECT_RATIO=9:16
IMAGE_SIZE=1K
```

Optional pricing overrides for the local estimators: `GEMINI_*_PRICE_PER_MILLION`,
`IMAGE_*_USD_PER_MILLION` (see `usage.py` and `social-post-image/image_usage.py`).

## Run (two terminals)

```powershell
# Terminal 1 — unified backend
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — React UI
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173/**  
Vite proxies `/api` → port 8000.

## What “Generate” does

1. **Generate post + poster** — parallel calls to text + image APIs (happy path:
   2 Vertex calls). Partial failure keeps whichever side succeeded.
2. **Regenerate** — text variation only; poster stays until you Generate again.
3. Optional **0–3 reference images** with roles (`product` / `style` / `brand` /
   `background` / `auto`) and an “Allow people in poster” opt-in (default off).

Store name is injected from the fixed demo selection — you do not need to type
it in every brief.

## Guardrails (high level)

- Vertex safety filters + facts-only prompts (no invented prices / % / dates)
- Input length limits and a light abuse blocklist
- Text output shape + light claim grounding
- Image: max 3 refs; people generation off unless opted in
- UI: “AI draft — review before posting”

Details: [`backend/README.md`](backend/README.md),
[`social-post-image/README.md`](social-post-image/README.md).

## Reports

- [`reports/AddLyft_Social_Post_Workflow_Audit.pdf`](reports/AddLyft_Social_Post_Workflow_Audit.pdf) —
  full Text + Image workflow audit (client-oriented)
- Regenerate:  
  `.\.venv\Scripts\python.exe reports\generate_social_post_workflow_audit.py`

## Out of scope

- Publishing / scheduling to social platforms
- Auth, multi-tenant quotas, production deployment
- Ad video / Veo (kept local-only; not in this repository)

## License / ownership

Internal AddLyft R&D — not an open-source product release.
