"""Generate social-post generation PDF report (Gemini Flash-Lite on Vertex AI)."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = Path("reports/social_post_generation_report.pdf")

GREEN = HexColor("#0f7a5f")
DARK = HexColor("#14201c")
MUTED = HexColor("#5b6b64")
LIGHT = HexColor("#fbfefc")
GRID = HexColor("#d5e0db")


def kv_table(rows: list[list[str]]) -> Table:
    data = [["Field", "Value"]] + rows
    t = Table(data, colWidths=[1.8 * inch, 4.9 * inch])
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
    t = Table(rows, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("BACKGROUND", (0, 1), (-1, 1), HexColor("#e8f5f0")),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="Social Post Generation Report — Gemini 2.5 Flash-Lite",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleMain",
            parent=styles["Title"],
            fontSize=14,
            spaceAfter=4,
            textColor=DARK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Sub",
            parent=styles["Normal"],
            fontSize=9.5,
            textColor=MUTED,
            spaceAfter=10,
            alignment=TA_CENTER,
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
            name="Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12.5,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=8,
            textColor=MUTED,
            leading=10.5,
        )
    )

    story = []
    story.append(
        Paragraph("AddLyft · Social Post Generation Report", styles["TitleMain"])
    )
    story.append(
        Paragraph(
            "Gemini 2.5 Flash-Lite on Vertex AI — how post generation is billed by tokens",
            styles["Sub"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=GRID, spaceAfter=8))

    story.append(Paragraph("A. Latest run (13 Sep 2026)", styles["H"]))
    story.append(
        Paragraph(
            "Fresh structured-output generation via "
            "<font face='Courier'>test_vertex_call.py</font> on Vertex AI. "
            "Brief: <i>20% off all yoga mats this weekend at ZenFit Studio.</i>",
            styles["Body"],
        )
    )
    story.append(
        kv_table(
            [
                ["Mode", "Text → structured social post (JSON schema)"],
                ["Timestamp (UTC)", "2026-09-13T13:54:08Z"],
                ["Model", "gemini-2.5-flash-lite"],
                ["Path", "Vertex AI (vertexai=True + ADC)"],
                ["Prompt tokens", "47"],
                ["Output tokens", "82"],
                ["Thoughts tokens", "0"],
                ["Total tokens", "129"],
                ["List-price estimate", "$0.00003750"],
                ["Log file", "logs/usage.jsonl"],
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Generated post:</b><br/>"
            "Caption: Get ready to flow! This weekend only, enjoy a special discount "
            "on all yoga mats at ZenFit Studio.<br/>"
            "Offer: 20% off all yoga mats<br/>"
            "CTA: Visit us this weekend!<br/>"
            "Hashtags: #ZenFitStudio #YogaMats #Sale #WeekendDeal #Yoga",
            styles["Body"],
        )
    )

    story.append(Paragraph("B. Is the cost fixed per post?", styles["H"]))
    story.append(
        Paragraph(
            "<b>No — cost is not a flat fee per post.</b> Gemini on Vertex AI bills "
            "<b>by tokens consumed</b> on each successful call. Longer briefs, system "
            "instructions, JSON schema overhead, and longer captions all increase tokens "
            "(and therefore cost). Shorter replies cost less. The dollar amount for a "
            "given post is only known after the model returns "
            "<font face='Courier'>usage_metadata</font>.",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "What <b>is</b> fixed are the <b>unit rates</b> (price per million tokens) "
            "for the chosen model. Those rates stay the same; the bill = rates × tokens.",
            styles["Body"],
        )
    )

    story.append(Paragraph("C. How billing depends on tokens", styles["H"]))
    story.append(
        Paragraph(
            "Each generation is split into token types. Flash-Lite rates used in this "
            "project’s estimator (<font face='Courier'>usage.py</font>):",
            styles["Body"],
        )
    )
    story.append(
        data_table(
            [
                ["Token type", "What it covers", "Rate (USD / 1M)"],
                ["Input (prompt)", "Brief + system text + schema", "$0.10"],
                ["Output", "Generated JSON (caption, offer, CTA, tags)", "$0.40"],
                ["Thoughts", "Hidden reasoning, if any (billed as output)", "$0.40"],
            ],
            [1.5 * inch, 3.2 * inch, 1.6 * inch],
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            "<b>Formula:</b><br/>"
            "<font face='Courier'>estimated_usd = (prompt_tokens × 0.10 + "
            "(output_tokens + thoughts_tokens) × 0.40) / 1,000,000</font><br/><br/>"
            "Latest run: (47 × 0.10 + 82 × 0.40) / 1,000,000 = <b>$0.0000375</b>.",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "Tokens are counted by Gemini and returned in the API response — we do not "
            "count characters by hand. Charges accrue on the GCP project’s linked "
            "billing account at Google’s list rates for the model.",
            styles["Body"],
        )
    )

    story.append(Paragraph("D. Logged post-generation runs", styles["H"]))
    story.append(
        Paragraph(
            "From <font face='Courier'>logs/usage.jsonl</font> (all "
            "<font face='Courier'>gemini-2.5-flash-lite</font>). Costs vary with token "
            "counts — same model, different bills:",
            styles["Body"],
        )
    )
    story.append(
        data_table(
            [
                ["When (UTC)", "Source", "P / O / Tot", "Est. USD"],
                ["2026-09-08 15:41", "test_vertex_call", "47 / 83 / 130", "$0.000038"],
                ["2026-09-08 17:32", "api_generate", "109 / 116 / 225", "$0.000057"],
                ["2026-09-08 17:32", "api_generate", "109 / 116 / 225", "$0.000057"],
                ["2026-09-08 17:33", "api_generate", "109 / 102 / 211", "$0.000052"],
                ["2026-09-08 17:35", "api_generate", "129 / 123 / 252", "$0.000062"],
                ["2026-09-08 17:56", "api_generate", "117 / 132 / 249", "$0.000065"],
                ["2026-09-08 18:19", "api_generate", "117 / 133 / 250", "$0.000065"],
                ["2026-09-13 13:54", "test_vertex_call", "47 / 82 / 129", "$0.000038"],
            ],
            [1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            "Observed range for this app: about <b>$0.000038</b> (short test brief) to "
            "about <b>$0.000065</b> (API path with system instruction). Still far under "
            "one tenth of a cent per post. API calls use more prompt tokens because the "
            "system instruction is included.",
            styles["Body"],
        )
    )

    story.append(Paragraph("E. Notes", styles["H"]))
    story.append(
        Paragraph(
            "• Tracking: <font face='Courier'>usage.py</font> + "
            "<font face='Courier'>backend/app/usage_log.py</font>; "
            "API returns usage on <font face='Courier'>/api/generate</font>.<br/>"
            "• Rates can be overridden via "
            "<font face='Courier'>GEMINI_INPUT_PRICE_PER_MILLION</font> / "
            "<font face='Courier'>GEMINI_OUTPUT_PRICE_PER_MILLION</font>.<br/>"
            "• Estimates use list rates; GCP Billing is the ledger of record.",
            styles["Body"],
        )
    )

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRID, spaceAfter=5))
    story.append(
        Paragraph(
            "AddLyft R&amp;D · Social post generation on Vertex AI · Updated 13 Sep 2026",
            styles["Small"],
        )
    )
    doc.build(story)
    print(path.resolve())


if __name__ == "__main__":
    build(OUT_PATH)
