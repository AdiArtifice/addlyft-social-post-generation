"""Generate complete Social Post Workflow audit PDF (Text + Image).

Sources: live codebase, logs/usage.jsonl, social-post-image/logs/image_usage.jsonl,
prior reports under reports/ and social-post-image/reports/.

Does not invent metrics — labels Measured / Configured estimate / Unknown.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = Path("reports/AddLyft_Social_Post_Workflow_Audit.pdf")

GREEN = HexColor("#0f7a5f")
DARK = HexColor("#14201c")
MUTED = HexColor("#5b6b64")
LIGHT = HexColor("#fbfefc")
GRID = HexColor("#d5e0db")
AMBER = HexColor("#8a5a00")
AMBER_BG = HexColor("#fff6e5")


def kv_table(rows: list[list[str]], col0: float = 1.9, col1: float = 4.8) -> Table:
    data = [["Field", "Value"]] + rows
    t = Table(data, colWidths=[col0 * inch, col1 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def data_table(rows: list[list[str]], col_widths: list[float]) -> Table:
    t = Table(rows, colWidths=[w * inch for w in col_widths])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def badge(text: str, styles) -> Paragraph:
    return Paragraph(
        f"<font color='#8a5a00'><b>[{text}]</b></font>",
        styles["Small"],
    )


def build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="AddLyft Social Post Workflow Audit — Text + Image",
        author="AddLyft R&D",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleMain",
            parent=styles["Title"],
            fontSize=13.5,
            spaceAfter=3,
            textColor=DARK,
            leading=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Sub",
            parent=styles["Normal"],
            fontSize=9,
            textColor=MUTED,
            spaceAfter=8,
            alignment=TA_CENTER,
            leading=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=11,
            spaceAfter=5,
            textColor=GREEN,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading3"],
            fontSize=9.5,
            spaceBefore=8,
            spaceAfter=3,
            textColor=DARK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontSize=8.8,
            leading=12,
            spaceAfter=5,
            alignment=TA_JUSTIFY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=7.8,
            textColor=MUTED,
            leading=10,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Note",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=AMBER,
            backColor=AMBER_BG,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
        )
    )

    story: list = []

    # --- Cover ---
    story.append(
        Paragraph(
            "AddLyft · Social Post Workflow Audit",
            styles["TitleMain"],
        )
    )
    story.append(
        Paragraph(
            "Complete Text + Image pipeline overview for client review<br/>"
            "Vertex AI · Gemini text + Nano Banana image · Local R&amp;D showcase<br/>"
            "Report date: 23 Sep 2026 · Scope: social-post only (video / Veo excluded)",
            styles["Sub"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=GRID, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>How to read this report.</b> Every cost and timing number is tagged: "
            "<b>Measured</b> = taken from this project’s usage logs; "
            "<b>Configured estimate</b> = calculated with the rates coded in the app "
            "(not a GCP invoice); "
            "<b>Unknown</b> = not recorded or not determined from the current implementation. "
            "Nothing here invents production SLAs or billing totals.",
            styles["Note"],
        )
    )

    # --- 1 Executive summary ---
    story.append(Paragraph("1. Executive summary", styles["H"]))
    story.append(
        Paragraph(
            "The Social Post Workflow turns a short advertising brief into two "
            "reviewable drafts in one screen: (1) structured social copy "
            "(caption, offer, CTA, hashtags) and (2) an optional portrait poster image, "
            "optionally guided by up to three reference photos. "
            "A fixed demo store identity (<b>AMPM Woodstock</b>) is applied automatically "
            "so the brief does not need to repeat the store name. "
            "Outputs are labeled AI drafts — the system does not publish to social networks.",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "On a successful “Generate post + poster” click, the UI calls two backend "
            "APIs <b>in parallel</b>: one Vertex text call and one Vertex image call "
            "(happy path = <b>2 model calls</b>). Regenerate updates text only "
            "(1 model call). Image generation dominates both time and cost.",
            styles["Body"],
        )
    )
    story.append(
        kv_table(
            [
                ["Primary UI", "http://127.0.0.1:5173/ (React)"],
                ["Unified API", "http://127.0.0.1:8000 (FastAPI)"],
                ["Text model", "gemini-2.5-flash-lite (Vertex)"],
                ["Image model", "gemini-3.1-flash-lite-image (Vertex, 9:16, 1K)"],
                [
                    "Typical combined cost (Configured estimate from Measured logs)",
                    "≈ $0.0345 per full generate (≈ $0.0001 text + ≈ $0.0344 image)",
                ],
                [
                    "Typical image latency (Measured)",
                    "≈ 8–11.5 seconds wall time (recent log samples)",
                ],
                [
                    "Text latency (Measured)",
                    "Unknown — text usage log does not record wall_seconds",
                ],
            ]
        )
    )

    # --- 2 Architecture ---
    story.append(Paragraph("2. Architecture and generation flow", styles["H"]))
    story.append(
        Paragraph(
            "User enters a brief (and optionally 0–3 reference images) in the React UI. "
            "Vite proxies <font face='Courier'>/api</font> to the FastAPI backend on port 8000. "
            "The backend owns both text generation and image generation "
            "(image logic reused from <font face='Courier'>social-post-image/</font>). "
            "A standalone image HTML page on port 8787 remains optional for debugging only.",
            styles["Body"],
        )
    )
    story.append(Paragraph("2.1 End-to-end steps (Generate)", styles["H2"]))
    bullets = [
        "Validate brief length / blocklist; apply selected store context (AMPM Woodstock).",
        "Start text + image requests together (parallel).",
        "Text: Gemini Flash-Lite returns JSON matching caption / offer / CTA / hashtags; "
        "output shape and claim checks run before response.",
        "Image: build role-aware poster prompt; resize refs; one Nano Banana image call; "
        "save poster + meta under social-post-image/outputs/.",
        "UI shows whichever side succeeded; errors are shown separately (partial failure OK).",
        "Compact usage strip: tokens / estimated cost (and time for image).",
    ]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(b, styles["BulletBody"]), leftIndent=8) for b in bullets],
            bulletType="1",
            start="1",
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>API call count (happy path).</b> Generate = 2 Vertex calls. "
            "Regenerate (text variation) = 1 Vertex text call. "
            "Text may retry once on non-safety failures (up to 2 text calls if transient error). "
            "Normal image generate is exactly one model call — no automatic edit pass.",
            styles["Body"],
        )
    )

    # --- 3 Models ---
    story.append(Paragraph("3. Models and their roles", styles["H"]))
    story.append(
        data_table(
            [
                ["Pipeline", "Model ID", "Role", "Source"],
                [
                    "Text",
                    "gemini-2.5-flash-lite",
                    "Structured social copy (JSON)",
                    "Configured default (GEMINI_MODEL)",
                ],
                [
                    "Image",
                    "gemini-3.1-flash-lite-image",
                    "9:16 poster (1K)",
                    "Configured default (IMAGE_MODEL)",
                ],
            ],
            [1.0, 2.3, 2.0, 1.6],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Text uses temperature 0.7 on first generate and 1.05 on regenerate "
            "(configured in code). Image aspect 9:16 and size 1K are configured defaults; "
            "the lite image model does not support 2K in this setup.",
            styles["Body"],
        )
    )

    # --- 4 APIs ---
    story.append(Paragraph("4. APIs and interfaces", styles["H"]))
    story.append(
        kv_table(
            [
                ["GET /api/health", "Service health + text model + store brand"],
                [
                    "POST /api/generate",
                    "JSON brief → caption, offer, CTA, hashtags + usage",
                ],
                [
                    "POST /api/generate-image",
                    "Multipart prompt + refs → base64 poster + usage",
                ],
                [
                    "Optional SPI UI",
                    "Port 8787 — image-only HTML (not required for showcase)",
                ],
            ]
        )
    )

    # --- 5 Cost / tokens / latency ---
    story.append(Paragraph("5. Tokens, latency, and cost", styles["H"]))
    story.append(
        Paragraph(
            "Costs below are <b>Configured estimates</b> using rates stored in the project "
            "(and matching root <font face='Courier'>.env</font>). "
            "They are not Google Cloud invoice lines. Token counts and image wall times "
            "are <b>Measured</b> from local JSONL logs.",
            styles["Body"],
        )
    )

    story.append(Paragraph("5.1 Unit rates used by the estimator", styles["H2"]))
    story.append(
        data_table(
            [
                ["Pipeline", "Token / unit type", "USD per 1M tokens", "Kind"],
                ["Text", "Input", "$0.10", "Configured estimate"],
                ["Text", "Output (+ thoughts)", "$0.40", "Configured estimate"],
                ["Image", "Input", "$0.25", "Configured estimate"],
                ["Image", "Text output", "$1.50", "Configured estimate"],
                ["Image", "Image output", "$30.00", "Configured estimate"],
            ],
            [1.0, 2.0, 1.6, 2.0],
        )
    )
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "Image size fallback table (when modality metadata is thin): "
            "1K ≈ 1120 image output tokens (configured in image_usage.py).",
            styles["Small"],
        )
    )

    story.append(Paragraph("5.2 Measured text samples (logs/usage.jsonl)", styles["H2"]))
    story.append(
        data_table(
            [
                ["When (UTC)", "Source", "Tokens (in/out/total)", "Est. USD", "Wall time"],
                [
                    "2026-09-22 19:41",
                    "api_generate",
                    "367 / 156 / 523",
                    "$0.000099",
                    "Unknown",
                ],
                [
                    "2026-09-22 19:33",
                    "api_generate",
                    "367 / 133 / 500",
                    "$0.000090",
                    "Unknown",
                ],
                [
                    "2026-09-13 13:54",
                    "test_vertex_call",
                    "47 / 82 / 129",
                    "$0.000038",
                    "Unknown",
                ],
            ],
            [1.4, 1.4, 1.7, 1.0, 1.0],
        )
    )
    story.append(
        Paragraph(
            "Model on these rows: gemini-2.5-flash-lite. Text wall_seconds is not logged "
            "→ latency Unknown for text.",
            styles["Small"],
        )
    )

    story.append(
        Paragraph(
            "5.3 Measured image samples (social-post-image/logs/image_usage.jsonl)",
            styles["H2"],
        )
    )
    story.append(
        data_table(
            [
                ["When (UTC)", "Source", "Total tokens", "Est. USD", "Wall (s)"],
                [
                    "2026-09-22 19:41",
                    "unified_ui_generate",
                    "4417",
                    "$0.03442",
                    "11.43",
                ],
                ["2026-09-21 18:40", "ui_generate", "4360", "$0.03441", "11.36"],
                ["2026-09-21 18:37", "ui_generate", "4360", "$0.03441", "11.07"],
                ["2026-09-21 18:31", "ui_generate", "1716", "$0.03375", "8.04"],
            ],
            [1.4, 1.6, 1.2, 1.1, 1.0],
        )
    )
    story.append(
        Paragraph(
            "Model on these rows: gemini-3.1-flash-lite-image · aspect 9:16 · size 1K. "
            "Older log lines may show historical Pro / 2K / 16:9 runs — those are "
            "not current defaults.",
            styles["Small"],
        )
    )

    story.append(Paragraph("5.4 What a full Generate typically costs", styles["H2"]))
    story.append(
        Paragraph(
            "Adding a recent Measured text estimate (~$0.0001) to a recent Measured "
            "image estimate (~$0.0344) gives roughly <b>$0.0345 per full generate</b> "
            "(Configured estimate from Measured token logs). "
            "Image is &gt;99% of that cost. Actual cloud bill may differ with "
            "promotions, discounts, or rate changes.",
            styles["Body"],
        )
    )

    # --- 6 I/O ---
    story.append(Paragraph("6. Input / output and processing", styles["H"]))
    story.append(Paragraph("6.1 Text pipeline", styles["H2"]))
    story.append(
        Paragraph(
            "<b>In:</b> freeform brief (max 2000 characters) + store_brand "
            "(fixed AMPM Woodstock in the demo UI). "
            "<b>Out:</b> caption, offer, CTA, 3–6 hashtags, usage. "
            "Processing: system “facts only” instructions, JSON schema enforcement, "
            "Vertex safety filters, then local checks (lengths, hashtag format, "
            "light claim grounding for $ / % style numbers).",
            styles["Body"],
        )
    )
    story.append(Paragraph("6.2 Image pipeline", styles["H2"]))
    story.append(
        Paragraph(
            "<b>In:</b> same brief + optional 0–3 reference images + per-image role "
            "(product / style / brand / background / auto) + allow-people flag + store. "
            "<b>Out:</b> poster image (base64), filename, usage (including wall time), "
            "person_generation mode used. "
            "Processing: build role-aware prompt, resize refs to max side 1600 JPEG, "
            "one image generate call, write outputs + meta JSON.",
            styles["Body"],
        )
    )

    # --- 7 References ---
    story.append(Paragraph("7. Reference-image handling", styles["H"]))
    story.append(
        kv_table(
            [
                ["Maximum references", "3 (enforced in UI and API)"],
                ["Optional?", "Yes — zero refs still allowed"],
                [
                    "Roles",
                    "product, brand, background, style, auto (default)",
                ],
                [
                    "Prep",
                    "Convert/resize to RGB JPEG, max side 1600px, quality 90",
                ],
                [
                    "Allowed types",
                    "jpg, jpeg, png, webp, heic, heif",
                ],
                [
                    "People / faces",
                    "Default ALLOW_NONE; user must opt in to ALLOW_ADULT "
                    "(no silent auto-upgrade)",
                ],
            ]
        )
    )

    # --- 8 Guardrails ---
    story.append(Paragraph("8. Guardrails and validation", styles["H"]))
    story.append(
        Paragraph(
            "Guardrails sit before and after the models — not only as polite prompt wording.",
            styles["Body"],
        )
    )
    g_bullets = [
        "<b>Input:</b> empty rejection, 2000-char cap, light abuse blocklist "
        "(e.g. fake reviews, weapons for sale), file type / ref count checks.",
        "<b>Vertex safety filters:</b> harassment, hate, sexually explicit, dangerous "
        "at BLOCK_MEDIUM_AND_ABOVE (configured).",
        "<b>Facts-only prompts:</b> do not invent prices, discounts, dates, or store "
        "details; selected store is injected as known context.",
        "<b>Text output checks:</b> required fields, length caps, 3–6 #hashtags, "
        "claim tokens ($ / % / “off”) must appear in the brief.",
        "<b>Image people policy:</b> no faces by default; explicit opt-in required.",
        "<b>Human review:</b> UI labels drafts “not published” with a short verify checklist.",
    ]
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph(b, styles["BulletBody"]), leftIndent=6)
                for b in g_bullets
            ],
            bulletType="bullet",
        )
    )

    # --- 9 Limitations ---
    story.append(Paragraph("9. Limitations, assumptions, and considerations", styles["H"]))
    lim = [
        "Local R&amp;D / client showcase — not a production publishing platform "
        "(no auth, tenant quotas, or Meta/TikTok post APIs).",
        "Store is a fixed demo default, standing in for a future “select store” step.",
        "Cost figures are estimator rates × logged tokens — not GCP Console invoices.",
        "No automatic OCR check that poster text matches the brief exactly.",
        "Text latency not recorded in usage.jsonl (Unknown).",
        "Image output token counts may use a size table / modality heuristic when "
        "provider metadata is incomplete.",
        "Claim grounding is lightweight regex — not full legal claim substantiation "
        "(advertiser still responsible under truth-in-advertising rules).",
        "Prior image MVP audit PDF and social-post token report remain useful "
        "background; this document reflects the unified Text+Image workflow as of "
        "23 Sep 2026.",
    ]
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph(b, styles["BulletBody"]), leftIndent=6)
                for b in lim
            ],
            bulletType="bullet",
        )
    )

    # --- 10 References ---
    story.append(Paragraph("10. Source materials used for this audit", styles["H"]))
    story.append(
        Paragraph(
            "Code: <font face='Courier'>backend/</font>, "
            "<font face='Courier'>frontend/</font>, "
            "<font face='Courier'>social-post-image/</font>, "
            "<font face='Courier'>usage.py</font>, "
            "<font face='Courier'>social-post-image/image_usage.py</font>. "
            "Measured logs: <font face='Courier'>logs/usage.jsonl</font>, "
            "<font face='Courier'>social-post-image/logs/image_usage.jsonl</font>. "
            "Prior docs: <font face='Courier'>reports/social_post_generation_report.pdf</font>, "
            "<font face='Courier'>social-post-image/reports/AddLyft_Social_Post_Image_MVP_Audit.pdf</font>, "
            "<font face='Courier'>reports/AddLyft_GCP_Vertex_AI_RnD_Technical_Reference.pdf</font> "
            "(context only; video sections out of scope).",
            styles["Body"],
        )
    )

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.6, color=GRID, spaceAfter=6))
    story.append(
        Paragraph(
            "AddLyft R&amp;D · Social Post Workflow Audit (Text + Image) · "
            "23 Sep 2026 · Estimator costs ≠ final cloud invoice",
            styles["Small"],
        )
    )

    doc.build(story)
    print(f"Wrote {path.resolve()}")


if __name__ == "__main__":
    build(OUT_PATH)
