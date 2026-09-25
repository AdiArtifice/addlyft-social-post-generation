"""Generate client-friendly Social Post Workflow audit PDF (Text + Image).

Simpler language + flow diagrams; keeps key tables and Measured / Configured /
Unknown metrics from logs and code. Does not invent numbers.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
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
GREEN_SOFT = HexColor("#e8f5f0")
DARK = HexColor("#14201c")
MUTED = HexColor("#5b6b64")
LIGHT = HexColor("#fbfefc")
GRID = HexColor("#d5e0db")
AMBER = HexColor("#8a5a00")
AMBER_BG = HexColor("#fff6e5")
BLUE = HexColor("#1a4f6e")
BLUE_SOFT = HexColor("#e8f1f6")
ORANGE = HexColor("#c45c26")
ORANGE_SOFT = HexColor("#f7ead8")


class DrawingFlowable(Flowable):
    """Wrap a ReportLab Drawing so it can sit in the Platypus story."""

    def __init__(self, drawing: Drawing):
        super().__init__()
        self.drawing = drawing
        self.width = drawing.width
        self.height = drawing.height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        self.drawing.drawOn(self.canv, 0, 0)


def _box(
    d: Drawing,
    x: float,
    y: float,
    w: float,
    h: float,
    fill,
    title: str,
    subtitle: str = "",
    title_size: float = 8.5,
):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=GRID, strokeWidth=0.8, rx=4, ry=4))
    d.add(
        String(
            x + w / 2,
            y + h / 2 + (3 if subtitle else 0),
            title,
            fontName="Helvetica-Bold",
            fontSize=title_size,
            fillColor=DARK,
            textAnchor="middle",
        )
    )
    if subtitle:
        d.add(
            String(
                x + w / 2,
                y + h / 2 - 9,
                subtitle,
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=MUTED,
                textAnchor="middle",
            )
        )


def _arrow_right(d: Drawing, x0: float, y: float, x1: float):
    d.add(Line(x0, y, x1 - 5, y, strokeColor=MUTED, strokeWidth=1.2))
    d.add(
        Polygon(
            [x1, y, x1 - 7, y + 3.5, x1 - 7, y - 3.5],
            fillColor=MUTED,
            strokeColor=MUTED,
            strokeWidth=0.5,
        )
    )


def _arrow_down(d: Drawing, x: float, y0: float, y1: float):
    d.add(Line(x, y0, x, y1 + 5, strokeColor=MUTED, strokeWidth=1.2))
    d.add(
        Polygon(
            [x, y1, x - 3.5, y1 + 7, x + 3.5, y1 + 7],
            fillColor=MUTED,
            strokeColor=MUTED,
            strokeWidth=0.5,
        )
    )


def flow_overall() -> DrawingFlowable:
    """Big-picture: brief → two parallel paths → drafts for review."""
    W, H = 500, 175
    d = Drawing(W, H)
    d.add(
        String(
            W / 2,
            H - 14,
            "What happens when you click Generate",
            fontName="Helvetica-Bold",
            fontSize=9,
            fillColor=DARK,
            textAnchor="middle",
        )
    )

    # Row 1: input
    _box(d, 175, 130, 150, 32, GREEN_SOFT, "Your ad brief", "+ optional photos")
    _arrow_down(d, 250, 130, 108)

    # Split label
    d.add(
        String(
            250,
            112,
            "runs together",
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=MUTED,
            textAnchor="middle",
        )
    )

    # Parallel row
    _box(d, 40, 58, 160, 42, BLUE_SOFT, "Text path", "Caption · Offer · CTA · Tags")
    _box(d, 300, 58, 160, 42, ORANGE_SOFT, "Image path", "Portrait poster (9:16)")

    d.add(Line(250, 108, 120, 100, strokeColor=MUTED, strokeWidth=1))
    d.add(Line(250, 108, 380, 100, strokeColor=MUTED, strokeWidth=1))

    # Into review
    _arrow_down(d, 120, 58, 36)
    _arrow_down(d, 380, 58, 36)
    d.add(Line(120, 36, 380, 36, strokeColor=MUTED, strokeWidth=1))
    _arrow_down(d, 250, 36, 30)
    _box(d, 155, 2, 190, 26, AMBER_BG, "You review the drafts", "Nothing is auto-posted")

    return DrawingFlowable(d)


def flow_text_detail() -> DrawingFlowable:
    W, H = 500, 78
    d = Drawing(W, H)
    boxes = [
        (8, "Brief + store", GREEN_SOFT),
        (108, "Safety checks", LIGHT),
        (208, "Gemini writes copy", BLUE_SOFT),
        (318, "Shape & claim checks", LIGHT),
        (418, "Post preview", AMBER_BG),
    ]
    bw, bh = 88, 36
    y = 22
    for i, (x, title, fill) in enumerate(boxes):
        _box(d, x, y, bw, bh, fill, title, title_size=7.5)
        if i < len(boxes) - 1:
            _arrow_right(d, x + bw, y + bh / 2, boxes[i + 1][0])
    d.add(
        String(
            W / 2,
            H - 12,
            "Text path (in order)",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            fillColor=DARK,
            textAnchor="middle",
        )
    )
    return DrawingFlowable(d)


def flow_image_detail() -> DrawingFlowable:
    W, H = 500, 78
    d = Drawing(W, H)
    boxes = [
        (8, "Brief + refs", GREEN_SOFT),
        (108, "Build poster prompt", LIGHT),
        (208, "Nano Banana image", ORANGE_SOFT),
        (318, "Save + usage", LIGHT),
        (418, "Poster preview", AMBER_BG),
    ]
    bw, bh = 88, 36
    y = 22
    for i, (x, title, fill) in enumerate(boxes):
        _box(d, x, y, bw, bh, fill, title, title_size=7.5)
        if i < len(boxes) - 1:
            _arrow_right(d, x + bw, y + bh / 2, boxes[i + 1][0])
    d.add(
        String(
            W / 2,
            H - 12,
            "Image path (in order)",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            fillColor=DARK,
            textAnchor="middle",
        )
    )
    return DrawingFlowable(d)


def flow_guardrails() -> DrawingFlowable:
    W, H = 500, 95
    d = Drawing(W, H)
    d.add(
        String(
            W / 2,
            H - 12,
            "Safety layers around the AI",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            fillColor=DARK,
            textAnchor="middle",
        )
    )
    _box(d, 20, 40, 110, 34, GREEN_SOFT, "1. Input checks", "length · blocklist")
    _arrow_right(d, 130, 57, 155)
    _box(d, 155, 40, 110, 34, BLUE_SOFT, "2. AI + filters", "facts-only · safety")
    _arrow_right(d, 265, 57, 290)
    _box(d, 290, 40, 110, 34, ORANGE_SOFT, "3. Output checks", "shape · claims")
    _arrow_right(d, 400, 57, 425)
    _box(d, 425, 40, 60, 34, AMBER_BG, "4. You", "approve")
    d.add(
        String(
            W / 2,
            12,
            "The app proposes drafts. A person still decides what goes live.",
            fontName="Helvetica",
            fontSize=7,
            fillColor=MUTED,
            textAnchor="middle",
        )
    )
    return DrawingFlowable(d)


def kv_table(rows: list[list[str]], col0: float = 1.9, col1: float = 4.8) -> Table:
    data = [["", ""]] + rows  # header replaced visually
    data[0] = ["Topic", "Detail"]
    t = Table(data, colWidths=[col0 * inch, col1 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
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


def build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="AddLyft Social Post Workflow — Client Overview",
        author="AddLyft R&D",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleMain",
            parent=styles["Title"],
            fontSize=14,
            spaceAfter=3,
            textColor=DARK,
            leading=17,
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
            spaceBefore=10,
            spaceAfter=5,
            textColor=GREEN,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading3"],
            fontSize=9.5,
            spaceBefore=7,
            spaceAfter=3,
            textColor=DARK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12.5,
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
            fontSize=8.2,
            leading=11.5,
            textColor=AMBER,
            backColor=AMBER_BG,
            borderPadding=7,
            spaceBefore=2,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletBody",
            parent=styles["Normal"],
            fontSize=8.6,
            leading=11.5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontSize=7.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8,
            spaceBefore=2,
        )
    )

    story: list = []

    story.append(Paragraph("AddLyft · Social Post Workflow", styles["TitleMain"]))
    story.append(
        Paragraph(
            "A plain-language overview of how text posts and poster images are created<br/>"
            "Client overview · 23 Sep 2026 · Social post only (video not included)",
            styles["Sub"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=GRID, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>How to read numbers in this document</b><br/>"
            "<b>Measured</b> = taken from our project usage logs · "
            "<b>Configured estimate</b> = calculated with the price rates coded in the app "
            "(helpful for planning; not a Google Cloud invoice) · "
            "<b>Unknown</b> = not recorded yet in this demo.",
            styles["Note"],
        )
    )

    # 1. In one minute
    story.append(Paragraph("1. In one minute", styles["H"]))
    story.append(
        Paragraph(
            "Someone on your team types a short promotion idea (the “brief”). "
            "The store is already set for this demo as <b>AMPM Woodstock</b>, "
            "so they do not need to repeat the store name every time. "
            "They can optionally upload up to three product or style photos.",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "One click creates <b>two drafts to review</b>: social-media wording "
            "(caption, offer, call-to-action, hashtags) and a vertical poster image. "
            "Nothing is posted automatically — a person still decides what goes live.",
            styles["Body"],
        )
    )
    story.append(kv_table([
        ["Primary screen", "Local showcase at http://127.0.0.1:5173/"],
        ["Text AI", "Gemini 2.5 Flash-Lite (Google Vertex AI)"],
        ["Image AI", "Nano Banana lite image model (9:16 portrait, 1K)"],
        [
            "Typical full generate cost",
            "About $0.0345 (Configured estimate from Measured logs: "
            "~$0.0001 text + ~$0.0344 image)",
        ],
        [
            "Typical poster wait time",
            "About 8–11.5 seconds (Measured from recent runs)",
        ],
        [
            "Text wait time",
            "Unknown in logs (not recorded for text yet)",
        ],
    ]))

    # 2. Big picture flow
    story.append(Paragraph("2. The big picture", styles["H"]))
    story.append(
        Paragraph(
            "Text writing and image creation run <b>at the same time</b> (in parallel). "
            "If one fails, the other can still succeed — you keep whatever worked.",
            styles["Body"],
        )
    )
    story.append(flow_overall())
    story.append(
        Paragraph(
            "Figure A — One brief feeds two drafts; you review before anything is published.",
            styles["Caption"],
        )
    )
    story.append(
        Paragraph(
            "<b>How many AI calls?</b> A normal Generate uses <b>2</b> model calls "
            "(one text, one image). “Regenerate” updates wording only (1 text call). "
            "The image path does not auto-edit; a correction would be a separate step.",
            styles["Body"],
        )
    )

    # 3. Text flow
    story.append(Paragraph("3. Text workflow (social copy)", styles["H"]))
    story.append(
        Paragraph(
            "The text path turns your brief into structured post fields that look like "
            "a finished social post in the preview — not raw JSON for the client to decode.",
            styles["Body"],
        )
    )
    story.append(flow_text_detail())
    story.append(Paragraph("Figure B — Text path, step by step.", styles["Caption"]))
    story.append(
        Paragraph(
            "<b>What you get:</b> caption, offer/key message, CTA button text, and "
            "3–6 hashtags. The selected store is added behind the scenes so the copy "
            "can mention AMPM Woodstock without you typing it in the brief.",
            styles["Body"],
        )
    )

    # 4. Image flow
    story.append(Paragraph("4. Image workflow (poster)", styles["H"]))
    story.append(
        Paragraph(
            "The image path builds a detailed creative brief for the image model, "
            "optionally using your photos as product or style guides, then returns "
            "one portrait poster.",
            styles["Body"],
        )
    )
    story.append(flow_image_detail())
    story.append(Paragraph("Figure C — Image path, step by step.", styles["Caption"]))
    story.append(kv_table([
        ["Format", "Portrait 9:16 · 1K (lite model limit)"],
        ["Photos", "0–3 optional · roles: product / style / brand / background / auto"],
        ["Photo prep", "Resized to max side 1600px JPEG before send"],
        [
            "People in the poster",
            "Off by default · turn on only if you want faces (Measured policy in product)",
        ],
        ["API calls per generate", "Exactly 1 image model call (happy path)"],
    ]))

    # 5. Cost & metrics
    story.append(Paragraph("5. Cost, tokens, and timing", styles["H"]))
    story.append(
        Paragraph(
            "Google bills AI usage mainly by how much text/image “work” each run uses "
            "(tokens). Longer briefs and reference photos usually mean more tokens. "
            "Our app shows estimated cost after each run using rates we configured "
            "for planning — useful for R&amp;D budgeting, not a substitute for the "
            "official cloud bill.",
            styles["Body"],
        )
    )
    story.append(Paragraph("5.1 Price rates used in the estimator", styles["H2"]))
    story.append(
        data_table(
            [
                ["Part", "What it covers", "USD / 1M tokens", "Kind"],
                ["Text input", "Brief + instructions", "$0.10", "Configured estimate"],
                ["Text output", "Generated post fields", "$0.40", "Configured estimate"],
                ["Image input", "Prompt + photo tokens", "$0.25", "Configured estimate"],
                ["Image pixels", "Generated poster", "$30.00", "Configured estimate"],
            ],
            [1.2, 2.0, 1.5, 1.8],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "For a 1K poster, the estimator often counts about <b>1120</b> image-output "
            "tokens when the provider does not return a finer split "
            "(Configured table in code).",
            styles["Small"],
        )
    )

    story.append(Paragraph("5.2 Recent text runs (from logs)", styles["H2"]))
    story.append(
        data_table(
            [
                ["When (UTC)", "Tokens in / out / total", "Est. USD", "Wait time"],
                ["2026-09-22 19:41", "367 / 156 / 523", "$0.000099", "Unknown"],
                ["2026-09-22 19:33", "367 / 133 / 500", "$0.000090", "Unknown"],
                ["2026-09-13 13:54", "47 / 82 / 129", "$0.000038", "Unknown"],
            ],
            [1.5, 2.2, 1.3, 1.3],
        )
    )
    story.append(
        Paragraph(
            "Measured token counts · Configured estimate dollars · model: gemini-2.5-flash-lite. "
            "Text wait time is Unknown (not stored in the text log).",
            styles["Small"],
        )
    )

    story.append(Paragraph("5.3 Recent poster runs (from logs)", styles["H2"]))
    story.append(
        data_table(
            [
                ["When (UTC)", "Total tokens", "Est. USD", "Wait (seconds)"],
                ["2026-09-22 19:41", "4417", "$0.03442", "11.43"],
                ["2026-09-21 18:40", "4360", "$0.03441", "11.36"],
                ["2026-09-21 18:37", "4360", "$0.03441", "11.07"],
                ["2026-09-21 18:31", "1716", "$0.03375", "8.04"],
            ],
            [1.5, 1.5, 1.5, 1.8],
        )
    )
    story.append(
        Paragraph(
            "Measured · model: gemini-3.1-flash-lite-image · 9:16 · 1K. "
            "Poster cost dominates a full Generate (over 99% of the combined estimate).",
            styles["Small"],
        )
    )

    story.append(Paragraph("5.4 Takeaway for budgeting", styles["H2"]))
    story.append(
        Paragraph(
            "Plan on roughly <b>three to four cents per full text+poster generate</b> "
            "at current lite settings (Configured estimate from Measured logs). "
            "Wording-only regenerates are far cheaper (fractions of a cent). "
            "Cloud discounts or rate changes can move the real invoice.",
            styles["Body"],
        )
    )

    # 6. Guardrails
    story.append(Paragraph("6. Guardrails — what the system protects", styles["H"]))
    story.append(
        Paragraph(
            "We do not rely on the AI “being careful” alone. Checks happen before and "
            "after generation, and the UI makes it clear these are drafts.",
            styles["Body"],
        )
    )
    story.append(flow_guardrails())
    story.append(Paragraph("Figure D — Four layers from input to human approval.", styles["Caption"]))
    story.append(
        ListFlowable(
            [
                ListItem(
                    Paragraph(
                        "<b>Input:</b> empty briefs rejected; 2000-character limit; "
                        "simple blocklist for clearly abusive asks; max 3 photos.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "<b>During AI:</b> Google safety filters for hate, harassment, "
                        "sexual, and dangerous content; “facts only” instructions "
                        "(no invented discounts or dates); store injected from selection.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "<b>After AI (text):</b> required fields, length limits, "
                        "hashtag formatting, light check that $ / % style claims "
                        "appeared in the brief.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "<b>You:</b> on-screen “draft — review before posting” checklist. "
                        "Legal proof for strong claims (e.g. “#1”) remains a business decision.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
            ],
            bulletType="bullet",
        )
    )

    # 7. Limits
    story.append(Paragraph("7. What this demo does not do (yet)", styles["H"]))
    story.append(
        ListFlowable(
            [
                ListItem(
                    Paragraph(
                        "It does not post to Instagram, Facebook, TikTok, or other networks.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "It is not a full multi-store app — store is fixed for the demo "
                        "(placeholder for a future “pick your store” step).",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "It does not automatically proofread every letter on the poster "
                        "(no OCR quality gate yet).",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "Estimated dollars are not the final Google Cloud invoice.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
                ListItem(
                    Paragraph(
                        "Ad video / Veo is out of scope for this social-post package.",
                        styles["BulletBody"],
                    ),
                    leftIndent=4,
                ),
            ],
            bulletType="bullet",
        )
    )

    # 8. Technical appendix (kept short but accurate)
    story.append(Paragraph("8. Technical snapshot (for your team)", styles["H"]))
    story.append(
        Paragraph(
            "Useful if engineering wants exact names. Clients can skip this section.",
            styles["Small"],
        )
    )
    story.append(kv_table([
        ["UI", "React (Vite) · port 5173 · proxies /api → 8000"],
        ["API", "FastAPI · POST /api/generate · POST /api/generate-image"],
        ["Text model ID", "gemini-2.5-flash-lite · Vertex · us-central1 (default)"],
        [
            "Image model ID",
            "gemini-3.1-flash-lite-image · Vertex · global · 9:16 · 1K",
        ],
        [
            "Logs used for Measured rows",
            "logs/usage.jsonl · social-post-image/logs/image_usage.jsonl",
        ],
        [
            "Related PDFs",
            "social_post_generation_report.pdf · "
            "AddLyft_Social_Post_Image_MVP_Audit.pdf (earlier image-only view)",
        ],
    ]))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.6, color=GRID, spaceAfter=6))
    story.append(
        Paragraph(
            "AddLyft R&amp;D · Social Post Workflow · Client overview · 23 Sep 2026 · "
            "Estimator costs ≠ final cloud invoice",
            styles["Small"],
        )
    )

    doc.build(story)
    print(f"Wrote {path.resolve()}")


if __name__ == "__main__":
    build(OUT_PATH)
