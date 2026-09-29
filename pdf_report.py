"""
Official PIXSpain PDF of the foundries currently shown on the map.
"""

import math
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ASSETS = Path(__file__).resolve().parent / "assets"
# White-background versions of the attached logos. The web app keeps its own files.
LOGO_PATH = ASSETS / "pdf" / "pixspain-logo.png"
FUNDING_PATH = ASSETS / "pdf" / "funding-partners.png"

SURFACE = HexColor("#3C5460")
GOLD = HexColor("#FAAA1E")
BURNT = HexColor("#EB5523")
CREAM = HexColor("#FCF0E4")
INK = HexColor("#1C1C1C")
LABEL = HexColor("#4E6270")
RULE = HexColor("#E4D5C6")
PAPER = HexColor("#FFFFFF")
CARD_LABEL_BG = HexColor("#F7F1EA")

PAGE_W, PAGE_H = A4
HEADER_FIRST = 36 * mm
HEADER_LATER = 14 * mm
FOOTER_H = 20 * mm
# Room above the gold rule for the page note, so body text cannot cover it.
NOTE_BAND = 7 * mm
SIDE = 14 * mm

TECH_LABELS = {
    "SiPh (Silicon Photonics)": "Silicon Photonics",
    "LN (Lithium Niobate)": "Lithium Niobate",
    "SiN (Silicon Nitride)": "Silicon Nitride",
    "Hybrid/Multi-platform": "Hybrid / Multi-platform",
}


def build_foundries_pdf(records) -> bytes:
    """Return a PDF of the filtered foundry records."""
    rows = _prepare_rows(records or [])
    generated = datetime.now()
    reference = f"PIX-{generated:%Y%m%d-%H%M}"

    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        title="PIXSpain Photonic Foundries — Filtered selection",
        author="PIXSpain",
        subject="Filtered photonic foundry profiles",
        creator="PIXSpain Photonic Foundries Map",
    )
    frame_width = PAGE_W - 2 * SIDE
    first_frame = Frame(
        SIDE,
        FOOTER_H + NOTE_BAND,
        frame_width,
        PAGE_H - HEADER_FIRST - FOOTER_H - NOTE_BAND,
        id="first",
        showBoundary=0,
    )
    later_frame = Frame(
        SIDE,
        FOOTER_H + NOTE_BAND,
        frame_width,
        PAGE_H - HEADER_LATER - FOOTER_H - NOTE_BAND,
        id="later",
        showBoundary=0,
    )
    doc.addPageTemplates([
        PageTemplate(
            id="First",
            frames=[first_frame],
            onPage=lambda canvas, _doc: _draw_chrome(
                canvas, _doc, generated, reference, large_header=True
            ),
        ),
        PageTemplate(
            id="Later",
            frames=[later_frame],
            onPage=lambda canvas, _doc: _draw_chrome(
                canvas, _doc, generated, reference, large_header=False
            ),
        ),
    ])

    styles = _styles()
    story = [NextPageTemplate("Later")]
    story.extend(_summary_block(rows, generated, reference, styles, frame_width))
    if rows:
        for index, row in enumerate(rows, start=1):
            story.append(Spacer(1, 3.2 * mm))
            story.append(KeepTogether(_foundry_card(row, index, styles, frame_width)))
    else:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(
            "No foundries match the current filters. Adjust the map filters and download again.",
            styles["body"],
        ))

    doc.build(story)
    return buffer.getvalue()


def _prepare_rows(records):
    rows = [row for row in records if isinstance(row, dict)]
    rows.sort(key=lambda row: (
        _text(row.get("country"), "").casefold(),
        _text(row.get("foundry"), "").casefold(),
    ))
    return rows


def _summary_block(rows, generated, reference, styles, width):
    countries = sorted({_text(row.get("country"), "") for row in rows if _text(row.get("country"), "")})
    commercial = sum(1 for row in rows if _text(row.get("type")) == "Commercial")
    count = len(rows)
    foundry_word = "foundry" if count == 1 else "foundries"
    country_word = "country" if len(countries) == 1 else "countries"

    if count:
        lead = (
            f"This document lists <b>{count}</b> {foundry_word} in "
            f"<b>{len(countries)}</b> {country_word}, matching the filters applied "
            f"in the PIXSpain Photonic Foundries Map on {generated:%d %B %Y}."
        )
    else:
        lead = (
            f"No foundries matched the filters applied in the PIXSpain Photonic "
            f"Foundries Map on {generated:%d %B %Y}."
        )

    intro = [
        Paragraph(lead, styles["body"]),
        Spacer(1, 2 * mm),
        Paragraph(
            "Indicative figures may vary by run and design. This extract is not a "
            "quotation or a commitment to accept a design. Contact technology@pixspain.es "
            "to confirm availability, schedule, and pricing.",
            styles["disclaimer"],
        ),
    ]
    if count:
        intro.append(Spacer(1, 3.5 * mm))
        stats = Table(
            [[
                _stat_cell(str(count), "Foundries", styles),
                _stat_cell(str(len(countries)), "Countries", styles),
                _stat_cell(str(commercial), "Commercial", styles),
                _stat_cell(reference, "Reference", styles),
            ]],
            colWidths=[width / 4.0] * 4,
        )
        stats.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_LABEL_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, SURFACE),
            ("LINEAFTER", (0, 0), (-2, -1), 0.3, RULE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        intro.append(stats)
        if countries:
            intro.append(Spacer(1, 2.2 * mm))
            intro.append(Paragraph(
                "Countries · " + ", ".join(countries),
                styles["meta"],
            ))
    return intro


def _stat_cell(value, label, styles):
    return [
        Paragraph(value, styles["stat_value"]),
        Paragraph(label.upper(), styles["stat_label"]),
    ]


def _foundry_card(row, index, styles, width):
    name = _esc(_text(row.get("foundry"), "Unnamed foundry"))
    country = _esc(_text(row.get("country"), "Unknown"))
    maturity = _esc(_text(row.get("type"), "Unspecified"))
    pairs = _profile_pairs(row)

    header = Table(
        [[
            Paragraph(f"{index}.  {name}", styles["card_name"]),
            Paragraph(f"{country}  ·  {maturity}", styles["card_meta"]),
        ]],
        colWidths=[width * 0.58, width * 0.42],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (1, 0), (1, 0), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    body_rows = [
        [
            Paragraph(_esc(label), styles["field_label"]),
            Paragraph(_esc(value), styles["field_value"]),
        ]
        for label, value in pairs
    ]
    label_w = 34 * mm
    body = Table(body_rows, colWidths=[label_w, width - label_w])
    body_style = [
        ("BACKGROUND", (0, 0), (0, -1), CARD_LABEL_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, RULE),
    ]
    body.setStyle(TableStyle(body_style))

    card = Table([[header], [body]], colWidths=[width])
    card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, SURFACE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _profile_pairs(row):
    technologies = row.get("technologies")
    if isinstance(technologies, list):
        platform = ", ".join(str(item) for item in technologies if _known(item))
    else:
        platform = _known(technologies)

    tech = _known(row.get("tech_category"))
    pairs = [
        ("Technology", TECH_LABELS.get(tech, tech)),
        ("Substrate", _known(row.get("substrate"))),
        ("Wavelength", _known(row.get("wavelength"))),
        ("Platform", platform or "Available on request"),
        ("Access", _known(row.get("access"))),
        ("Applications", _known(row.get("applications"))),
        ("Schedule", _format_schedule(row.get("schedule"))),
    ]
    status = _optional_text(row.get("status"))
    if status:
        pairs.append(("Status", status))
    for label, key in (
        ("Positioning", "market_positioning"),
        ("Payment", "payment_terms"),
        ("IP licensing", "ip_licensing"),
    ):
        value = _optional_text(row.get(key))
        if value:
            pairs.append((label, value))

    price = _money(row.get("mpw_price_usd"))
    if price:
        pairs.append(("Indicative MPW", price))
    lead = _weeks(row.get("lead_time_weeks"))
    if lead:
        pairs.append(("Lead time", lead))
    return [(label, value) for label, value in pairs if value]


def _format_schedule(schedule) -> str:
    if not isinstance(schedule, dict) or not schedule:
        return "On request"
    overall = _known(schedule.get("all"))
    if overall:
        return overall
    skip = {"TBA", "Unknown", "On-demand", "Dedicated"}
    items = []
    for month, value in schedule.items():
        if month == "all":
            continue
        text = _known(value)
        if text and text not in skip:
            items.append(f"{month}: {text}")
    return "; ".join(items) if items else "On request"


_ASPECT_CACHE = {}


def _aspect(path: Path) -> float:
    key = str(path)
    cached = _ASPECT_CACHE.get(key)
    if cached:
        return cached
    ratio = 4.5
    try:
        from PIL import Image
        with Image.open(path) as image:
            width, height = image.size
            if height:
                ratio = width / height
    except OSError:
        pass
    _ASPECT_CACHE[key] = ratio
    return ratio


def _draw_chrome(canvas, doc, generated, reference, large_header):
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    _draw_footer(canvas)
    if large_header:
        _draw_first_header(canvas, generated, reference)
    else:
        _draw_running_header(canvas, reference)
    canvas.restoreState()


def _draw_first_header(canvas, generated, reference):
    top = PAGE_H
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.6)
    canvas.line(SIDE, top - HEADER_FIRST, PAGE_W - SIDE, top - HEADER_FIRST)

    logo_h = 14 * mm
    logo_w = logo_h * _aspect(LOGO_PATH)
    logo_x = 12 * mm
    logo_y = top - HEADER_FIRST + (HEADER_FIRST - logo_h) / 2
    if LOGO_PATH.exists():
        canvas.drawImage(
            str(LOGO_PATH),
            logo_x,
            logo_y,
            width=logo_w,
            height=logo_h,
            mask="auto",
            preserveAspectRatio=True,
            anchor="sw",
        )

    text_x = logo_x + logo_w + 5 * mm
    canvas.setFillColor(BURNT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(text_x, top - 13.2 * mm, "OFFICIAL EXTRACT")
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(text_x, top - 19.2 * mm, "Photonic Foundries Map")
    canvas.setFillColor(LABEL)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(text_x, top - 24.2 * mm, "Filtered selection report")

    canvas.setFillColor(INK)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - 12 * mm, top - 14 * mm, generated.strftime("%d %B %Y"))
    canvas.setFillColor(LABEL)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - 12 * mm, top - 18.4 * mm, reference)
    canvas.drawRightString(PAGE_W - 12 * mm, top - 22.8 * mm, "technology@pixspain.es")


def _draw_running_header(canvas, reference):
    top = PAGE_H
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(SIDE, top - HEADER_LATER, PAGE_W - SIDE, top - HEADER_LATER)

    logo_h = 8 * mm
    logo_w = logo_h * _aspect(LOGO_PATH)
    if LOGO_PATH.exists():
        canvas.drawImage(
            str(LOGO_PATH),
            12 * mm,
            top - HEADER_LATER + (HEADER_LATER - logo_h) / 2,
            width=logo_w,
            height=logo_h,
            mask="auto",
            preserveAspectRatio=True,
            anchor="sw",
        )
    canvas.setFillColor(LABEL)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        PAGE_W - 12 * mm,
        top - 8.6 * mm,
        f"Photonic Foundries Map   ·   {reference}",
    )


def _draw_footer(canvas):
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(SIDE, FOOTER_H, PAGE_W - SIDE, FOOTER_H)

    caption = Paragraph(
        "Co-funded by the European Union · Chips JU · NextGenerationEU · "
        "Ministerio para la Transformación Digital y de la Función Pública · "
        "Plan de Recuperación, Transformación y Resiliencia",
        ParagraphStyle(
            "funding_caption",
            fontName="Helvetica",
            fontSize=6.4,
            leading=8,
            textColor=LABEL,
            alignment=TA_CENTER,
        ),
    )
    caption_w = PAGE_W - 20 * mm
    caption.wrap(caption_w, 12 * mm)

    max_w = 142 * mm
    image_h = 7.6 * mm
    image_w = image_h * _aspect(FUNDING_PATH)
    if image_w > max_w:
        image_w = max_w
        image_h = image_w / _aspect(FUNDING_PATH)
    image_x = (PAGE_W - image_w) / 2
    image_y = 2.2 * mm
    if FUNDING_PATH.exists():
        canvas.drawImage(
            str(FUNDING_PATH),
            image_x,
            image_y,
            width=image_w,
            height=image_h,
            mask="auto",
            preserveAspectRatio=True,
            anchor="sw",
        )
    caption.drawOn(canvas, 10 * mm, image_y + image_h + 1.1 * mm)

    canvas.setFillColor(LABEL)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(SIDE, FOOTER_H + 2.4 * mm, "Indicative information  ·  technology@pixspain.es")
    canvas.drawRightString(PAGE_W - SIDE, FOOTER_H + 2.4 * mm, f"Page {canvas.getPageNumber()}")


def _styles():
    return {
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=LABEL,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=LABEL,
        ),
        "stat_value": ParagraphStyle(
            "stat_value",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=SURFACE,
            alignment=TA_LEFT,
        ),
        "stat_label": ParagraphStyle(
            "stat_label",
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=LABEL,
            alignment=TA_LEFT,
        ),
        "card_name": ParagraphStyle(
            "card_name",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=CREAM,
        ),
        "card_meta": ParagraphStyle(
            "card_meta",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=CREAM,
            alignment=TA_RIGHT,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=LABEL,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
    }


def _text(value, default="—"):
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "n/a", "null"}:
        return default
    return text


def _known(value) -> str:
    text = _text(value, "")
    if text.lower() in {"unknown", "n/a", "none", "nan", "null"}:
        return ""
    return text


def _optional_text(value):
    return _known(value) or None


def _money(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(amount) or amount == 0:
        return None
    return f"USD {amount:,.0f}"


def _weeks(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        weeks = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(weeks) or weeks <= 0:
        return None
    shown = int(weeks) if weeks.is_integer() else round(weeks, 1)
    return f"{shown} weeks"


def _esc(value) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
