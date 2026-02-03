# src/pdf_utils.py
from __future__ import annotations

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

from src.invoice_generator import Invoice
from src.themes import load_theme


PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm

TABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

COL_DESC = LEFT_MARGIN
COL_QTY = LEFT_MARGIN + TABLE_WIDTH * 0.62
COL_UNIT = LEFT_MARGIN + TABLE_WIDTH * 0.74
COL_TOTAL = LEFT_MARGIN + TABLE_WIDTH * 0.90

TOTALS_MIN_Y = BOTTOM_MARGIN + 55 * mm

HEADER_HEIGHT = 36 * mm
HEADER_TOP_PADDING = 6 * mm
META_LINE_GAP = 12

MAX_LOGO_WIDTH = 45 * mm
MAX_LOGO_HEIGHT = 22 * mm


def generate_invoice_pdf(
    invoice: Invoice,
    output_path: str,
    theme_name: str = "minimal",
    theme_override: str | None = None,
) -> None:
    theme = load_theme(theme_name, theme_override)

    c = canvas.Canvas(output_path, pagesize=A4)
    y = PAGE_HEIGHT - TOP_MARGIN

    desc_style = ParagraphStyle(
        name="Description",
        fontName=theme["font"],
        fontSize=theme["base_font_size"],
        leading=theme["line_height"] + 2,
        alignment=TA_LEFT,
    )

    y = _draw_header(c, invoice, y, theme)
    y -= 18

    y = _draw_parties(c, invoice, y, theme)
    y -= 24

    y = _draw_line_items(c, invoice, y, theme, desc_style)

    totals_y = max(y - 24, TOTALS_MIN_Y)
    _draw_totals(c, invoice, totals_y, theme)

    if invoice.notes:
        _draw_notes(c, invoice.notes, totals_y - 40, theme)

    _draw_footer(c, invoice, theme)

    c.showPage()
    c.save()


# ---------------- Header ----------------
def _draw_header(c, invoice: Invoice, y: float, theme) -> float:
    header_bottom = y - HEADER_HEIGHT
    content_y = y - HEADER_TOP_PADDING

    logo_width = 0

    if invoice.company.logo_path:
        path = invoice.company.logo_path
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if os.path.exists(path):
            img = ImageReader(path)
            iw, ih = img.getSize()
            scale = min(MAX_LOGO_HEIGHT / ih, MAX_LOGO_WIDTH / iw)
            logo_width = iw * scale
            logo_height = ih * scale

            c.drawImage(
                img,
                LEFT_MARGIN,
                content_y - logo_height + 4,
                width=logo_width,
                height=logo_height,
                mask="auto",
            )

    text_x = LEFT_MARGIN + logo_width + (10 if logo_width else 0)

    c.setFont(theme["font_bold"], theme["header_font_size"])
    c.setFillColor(theme["text"])
    c.drawString(text_x, content_y, invoice.company.name)

    c.setFont(theme["font"], theme["base_font_size"])
    c.setFillColor(theme["muted"])
    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        content_y,
        f"Invoice #{invoice.invoice_number}",
    )
    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        content_y - META_LINE_GAP,
        f"Date: {invoice.invoice_date}",
    )

    c.setStrokeColor(theme["accent"])
    c.setLineWidth(1)
    c.line(
        LEFT_MARGIN,
        header_bottom + 6,
        PAGE_WIDTH - RIGHT_MARGIN,
        header_bottom + 6,
    )

    return header_bottom


# ---------------- Parties ----------------
def _draw_parties(c, invoice: Invoice, y: float, theme) -> float:
    left_x = LEFT_MARGIN
    right_x = PAGE_WIDTH / 2 + 10

    c.setFont(theme["font_bold"], theme["base_font_size"] + 1)
    c.drawString(left_x, y, "Bill From")
    c.drawString(right_x, y, "Bill To")

    y -= theme["line_height"] + 6
    left_h = _draw_party_block(c, invoice.company, left_x, y, theme)
    right_h = _draw_party_block(c, invoice.client, right_x, y, theme)

    return y - max(left_h, right_h)


def _draw_party_block(c, party, x: float, y: float, theme) -> float:
    c.setFont(theme["font"], theme["base_font_size"])
    offset = 0

    c.drawString(x, y, party.name)
    offset += theme["line_height"]

    for line in party.address.split("\n"):
        c.drawString(x, y - offset, line)
        offset += theme["line_height"]

    if party.email:
        c.drawString(x, y - offset, party.email)
        offset += theme["line_height"]

    return offset


# ---------------- Line Items ----------------
def _draw_line_items(c, invoice: Invoice, y: float, theme, desc_style) -> float:
    def draw_header(y_pos):
        c.setFont(theme["font_bold"], theme["base_font_size"])
        c.drawString(COL_DESC, y_pos, "Description")
        c.drawRightString(COL_QTY, y_pos, "Qty")
        c.drawRightString(COL_UNIT, y_pos, "Unit Price")
        c.drawRightString(COL_TOTAL, y_pos, "Amount")

        c.setStrokeColor(theme["accent"])
        c.line(
            LEFT_MARGIN,
            y_pos - theme["rule_gap"],
            PAGE_WIDTH - RIGHT_MARGIN,
            y_pos - theme["rule_gap"],
        )

        return y_pos - theme["line_height"] - theme["rule_gap"]

    y = draw_header(y)

    for item in invoice.line_items:
        desc = Paragraph(item.description, desc_style)
        avail_width = COL_QTY - COL_DESC - 8
        _, desc_h = desc.wrap(avail_width, PAGE_HEIGHT)

        row_height = max(desc_h, theme["line_height"]) + theme["row_padding"]

        if y - row_height < BOTTOM_MARGIN + 70:
            c.showPage()
            y = PAGE_HEIGHT - TOP_MARGIN
            y = _draw_header(c, invoice, y, theme)
            y -= 18
            y = _draw_parties(c, invoice, y, theme)
            y -= 24
            y = draw_header(y)

        desc.drawOn(c, COL_DESC, y - desc_h + 4)

        c.setFont(theme["font"], theme["base_font_size"])
        c.drawRightString(COL_QTY, y, str(item.quantity))
        c.drawRightString(COL_UNIT, y, _fmt_money(item.unit_price, theme))
        c.drawRightString(COL_TOTAL, y, _fmt_money(item.line_total, theme))

        y -= row_height

    return y


def _fmt_money(value: float, theme) -> str:
    return f'{theme["currency_symbol"]}{value:,.2f}'


# ---------------- Totals ----------------
def _draw_totals(c, invoice: Invoice, y: float, theme) -> None:
    label_x = COL_UNIT
    value_x = COL_TOTAL

    c.setFont(theme["font"], theme["base_font_size"])
    c.drawRightString(label_x, y, "Subtotal")
    c.drawRightString(value_x, y, _fmt_money(invoice.subtotal, theme))

    y -= theme["line_height"]
    tax_label = f"{invoice.tax_label} ({int(invoice.tax_rate * 100)}%)"
    c.drawRightString(label_x, y, tax_label)
    c.drawRightString(value_x, y, _fmt_money(invoice.tax_amount, theme))

    y -= theme["line_height"] + 8
    c.setFont(theme["font_bold"], theme["base_font_size"] + 1)
    c.setFillColor(theme["accent"])
    c.drawRightString(label_x, y, "Total")
    c.drawRightString(value_x, y, _fmt_money(invoice.total, theme))
    c.setFillColor(theme["text"])


# ---------------- Notes ----------------
def _draw_notes(c, notes: str, y: float, theme) -> None:
    c.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)

    y -= 14
    c.setFont(theme["font_bold"], theme["base_font_size"])
    c.drawString(LEFT_MARGIN, y, "Notes")

    y -= theme["line_height"]
    c.setFont(theme["font"], theme["base_font_size"])
    c.drawString(LEFT_MARGIN, y, notes)


# ---------------- Footer ----------------
def _draw_footer(c, invoice: Invoice, theme) -> None:
    if not invoice.footer:
        return

    c.setFont(theme["font"], 8)
    c.setFillColor(theme["muted"])
    c.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 8, invoice.footer)
    c.setFillColor(theme["text"])
