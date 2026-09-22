# Social Post Generation (unified UI)

R&D showcase at **http://127.0.0.1:5173/**: one brief → structured social copy
(`caption`, `offer`, `cta`, `hashtags`) **and** a poster image (optional 0–3
reference uploads). Does **not** publish to social platforms.

## Run locally (two processes)

From the repo root:

```powershell
# Terminal 1 — unified backend (text + image APIs on port 8000)
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — React UI
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173/** only. Vite proxies `/api` → `8000`.

The standalone image HTML app on port 8787 (`social-post-image/`) remains
available for debugging but is not required for the showcase.

## What Generate does

- **Generate post + poster** — calls `/api/generate` and `/api/generate-image` in
  parallel. Partial failure keeps whichever side succeeded.
- **Regenerate** — text variation only; poster stays until you Generate again.
- Refs: up to 3 images with roles (`auto` / `product` / `style` / `brand` /
  `background`) and optional “Allow people in poster”.

## Guardrails — system vs user

### System enforces

- Vertex **safety filters** (hate, harassment, sexually explicit, dangerous) at medium+
- **Facts-only** system instruction: no invented prices, %, dates, or store details
- Max brief length (2000 chars) and a light abuse **blocklist**
- Output shape: required fields, 3–6 `#` hashtags, field length caps
- Claim grounding: `$` / `%` / “off” style numbers in the output must appear in the brief
- Image: max 3 refs, `person_generation=ALLOW_NONE` unless opted in
- UI labels output as an **AI draft** (not published)

### User is responsible for

- Creative tone, humor, and CTA style
- Which promotion / product to run
- Final “yes, post this” decision
- Legal claim substantiation (software cannot certify “#1” or health claims)
- Hashtag strategy beyond format
- Whether people appear in the poster
- Not pasting customer PII into the brief

### Deferred (not in this demo)

Auth, per-user quotas, second-model moderation, OCR QA, and publishing APIs.

## Env (repo root `.env`)

```env
GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash-lite
IMAGE_MODEL=gemini-3.1-flash-lite-image
IMAGE_LOCATION=global
IMAGE_ASPECT_RATIO=9:16
IMAGE_SIZE=1K
```
