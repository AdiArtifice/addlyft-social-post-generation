# Social Post Image Generation (Nano Banana / Vertex AI)

R&D: generate **one** professional social-media ad poster from a natural-language prompt + **0–3 user-selected** reference images via Vertex AI.

| Setting | Value |
|---|---|
| Model | `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite) |
| Aspect | `9:16` |
| Size | `1K` (lite model max; Pro/Flash can use `2K`) |
| Store brand default | **AMPM Woodstock** (unless the prompt names another retailer) |
| Max refs | **3** (any mix; none required) |
| API calls | **One** per normal generate |

Does **not** generate captions/hashtags or touch the text social-post / Veo apps.

## Guardrails — system vs user

### System enforces

- Vertex **safety filters** (text + image harm categories) at medium+
- **Facts-only** prompt rules: no invented offers, prices, dates, or contact details
- Max prompt length (2000 chars) and a light abuse **blocklist**
- Max **3** reference images; per-ref roles (`product` / `style` / `brand` / `background` / `auto`)
- Default `person_generation=ALLOW_NONE` — **no silent upgrade** to allow people; UI checkbox or CLI `--allow-people` required
- UI labels output as an **AI draft** with a verify checklist (offer, brand, spelling)

### User is responsible for

- Creative direction and which promotion to run
- Choosing reference roles and whether people may appear
- Final “yes, use this poster” decision and claim substantiation
- Not pasting customer PII into the prompt

### Deferred (not in this demo)

Auth, OCR verification that poster text matches the brief, and publishing APIs.

## Single-call policy

- **Normal generate** = exactly **one** Nano Banana API call. No automatic second edit call.
- **Edit** (CLI only) is a **separate** correction via `--edit --image PATH`.

## Minimal UI (prompt + refs → image)

> **Primary showcase:** use the React app at **http://127.0.0.1:5173/** (backend
> on port 8000). It combines text + poster in one UI. This standalone page is
> optional for image-only debugging.

Prove the visual flow locally:

```powershell
cd social-post-image
..\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8787
```

Open http://127.0.0.1:8787/

1. Enter / edit the natural-language prompt (seeded from `promotion.json` → `user_prompt`)
2. Optionally upload up to 3 reference images
3. Click **Generate**
4. View the final poster (one API call)

## Prerequisites

1. Same GCP project + ADC (`gcloud auth application-default login`)
2. Vertex AI API enabled
3. Root `.env` includes `IMAGE_*` variables

## Env (repo root `.env`)

```env
IMAGE_MODEL=gemini-3.1-flash-lite-image
IMAGE_LOCATION=global
IMAGE_ASPECT_RATIO=9:16
IMAGE_SIZE=1K
IMAGE_INPUT_USD_PER_MILLION=0.25
IMAGE_TEXT_OUTPUT_USD_PER_MILLION=1.50
IMAGE_OUTPUT_USD_PER_MILLION=30.00
```

> **Note:** `gemini-3.1-flash-lite-image` supports **1K only**. Requesting `2K` returns `400 INVALID_ARGUMENT`. Default social aspect is **9:16** (Stories/Reels). Use `16:9` only when you explicitly want landscape.

## Promotion

`promotion.json` seeds the UI via `user_prompt` (primary). Structured fields remain for CLI compatibility.

The **entered prompt** is the source of truth for product, offer, required text, and instructions. Reference images guide product fidelity, branding, environment, style, or composition as appropriate.

## Reference images (0–3)

| Role | Use |
|---|---|
| `product` | Exact product pack / branding |
| `brand` | AMPM Woodstock visual cues |
| `background` | Store / shelf / cooler environment |
| `style` | Layout / typography / lighting inspiration only (do not copy products or offers) |
| `auto` | Model inspects content and applies appropriately |

Filename prefixes (`product_`, `brand_`, `background_` / `bg_`, `style_`) also set the role in the CLI when no hint is given.

The **UI** lets you pick a role per uploaded reference (defaults to `auto`).

### CLI — generate (one API call)

```powershell
.\.venv\Scripts\python.exe social-post-image\generate_poster.py

.\.venv\Scripts\python.exe social-post-image\generate_poster.py `
  --ref references\New\product_shelf.jpg:product `
  --ref references\New\style_ad.jpg:style
```

### CLI — edit (separate correction, one API call)

```powershell
.\.venv\Scripts\python.exe social-post-image\generate_poster.py `
  --edit `
  --image social-post-image\outputs\poster_YYYYMMDDTHHMMSSZ.jpg `
  --edit-notes "Fix offer spelling only"
```

### selection.json

Copy `references/selection.example.json` → `references/selection.json` and edit. Used when `--ref` is omitted.

More than 3 refs is rejected. The pipeline never auto-sends every file in the folder.

## Outputs

`social-post-image/outputs/` — image + `*_meta.json` (includes usage, prompt).

Usage log: `social-post-image/logs/image_usage.jsonl`.

## Notes

- Default `person_generation` is `ALLOW_NONE`. If a reference contains people and generation is blocked, enable **Allow people in poster** (UI) or pass `--allow-people` (CLI). There is **no** automatic silent retry with `ALLOW_ADULT`.
- Auth is Vertex-only (`vertexai=True` + ADC).
