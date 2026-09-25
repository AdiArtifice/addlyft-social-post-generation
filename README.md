# AddLyft — Social Post Generation

R&D showcase that turns a short ad brief into a **ready-to-review social post**:
portrait poster **plus** caption / offer / CTA / hashtags in one phone-style
draft card.

This repo is the **social-post deliverable only**. Ad video / Veo work is not
included.

| | |
|---|---|
| Primary UI | http://127.0.0.1:5173/ |
| Backend API | http://127.0.0.1:8000 |
| Text / vision model | `gemini-2.5-flash-lite` (Vertex AI) |
| Image model | `gemini-3.1-flash-lite-image` (9:16, 1K) |
| Demo store | Fixed **AMPM Woodstock** (stands in for a prior store-select step) |

Outputs are **AI drafts** — nothing is published to social platforms.

## Repo layout

```
backend/                 # FastAPI: /api/generate-pipeline (+ generate, generate-image, reports)
frontend/                # React (Vite) phone-frame showcase UI
social-post-image/       # Image engine (prompts, Vertex client); optional :8787 UI
reports/                 # Social-post audit / token reports (PDF + generators)
references/              # Sample reference images for demos
usage.py                 # Text token cost estimator + logger (incl. pipeline totals)
logs/usage.jsonl         # Local usage log (gitignored) — pipeline / regenerate totals
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

## Generation pipeline

**Generate** runs one sequential workflow (`POST /api/generate-pipeline`):

1. **Optimize** — Flash-Lite rewrites the raw brief into a concise image-ready
   prompt (facts preserved; fluff removed).
2. **Image** — Nano Banana image model builds the 9:16 poster from that prompt
   plus optional **0–3 reference images** (roles: `product` / `style` / `brand` /
   `background` / `auto`). “Allow people in poster” defaults off.
3. **Vision caption** — Flash-Lite sees the **raw brief + generated poster** and
   returns caption, offer, CTA, and hashtags (3–6).

Happy path: **3 Vertex calls**. If caption fails after a successful poster, the
UI still shows the poster.

**Regenerate** (`POST /api/generate` with the existing poster + `variation=true`):
new caption / offer / CTA / hashtags from brief + poster (**1** vision call).
The poster does not change.

Store name is injected from the fixed demo selection — you do not need to type
it in every brief.

### UI

- One **phone-frame** draft card: poster (height-capped, `object-fit: contain`)
  then caption → offer → CTA → hashtags.
- Click the poster to open a full-size lightbox.
- Cost / token / model metrics are **not** shown in the main UI.

## API surface (backend)

| Endpoint | Role |
|---|---|
| `POST /api/generate-pipeline` | Full Generate: optimize → image → vision caption |
| `POST /api/generate-image` | Image-only (used internally; still available) |
| `POST /api/generate` | Text or vision caption; Regenerate sends `image_base64` |
| `GET /api/generation-reports?limit=20` | Newest pipeline / regenerate totals from `logs/usage.jsonl` |
| `GET /api/health` | Liveness + configured text model / store |

Each successful Generate appends an `api_pipeline` total row (wall time, tokens,
estimated USD, models, per-step breakdown). Each Regenerate appends
`api_regenerate`.

## Guardrails (high level)

- Vertex safety filters + facts-only prompts (no invented prices / % / dates)
- Input length limits, optimized-prompt length cap, and a light abuse blocklist
- Text output shape + light claim grounding against the **raw brief**
- Image: max 3 refs; people generation off unless opted in
- UI: “AI draft — review before posting”

Details: [`backend/README.md`](backend/README.md),
[`social-post-image/README.md`](social-post-image/README.md).

## Reports

- Live totals: `GET http://127.0.0.1:8000/api/generation-reports?limit=20`
- Offline audit PDF:
  [`reports/AddLyft_Social_Post_Workflow_Audit.pdf`](reports/AddLyft_Social_Post_Workflow_Audit.pdf)
- Regenerate the PDF:  
  `.\.venv\Scripts\python.exe reports\generate_social_post_workflow_audit.py`

## Out of scope

- Publishing / scheduling to social platforms
- Auth, multi-tenant quotas, production deployment
- Ad video / Veo (kept local-only; not in this repository)

## License / ownership

Internal AddLyft R&D — not an open-source product release.
