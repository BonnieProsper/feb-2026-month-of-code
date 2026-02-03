from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import os
from src.invoice_generator import Invoice

# ================= Layout Constants =================
PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm

LINE_HEIGHT = 12

MAX_LOGO_WIDTH = 45 * mm
MAX_LOGO_HEIGHT = 22 * mm

TABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

COL_DESC = LEFT_MARGIN
COL_QTY = LEFT_MARGIN + TABLE_WIDTH * 0.62
COL_UNIT = LEFT_MARGIN + TABLE_WIDTH * 0.74
COL_TOTAL = LEFT_MARGIN + TABLE_WIDTH * 0.90

TOTALS_MIN_Y = BOTTOM_MARGIN + 55 * mm

HEADER_HEIGHT = 30 * mm
ROW_PADDING = 6
RULE_GAP = 8
TEXT_GAP = 4

CURRENCY_SYMBOL = "$"  # later configurable

DESC_STYLE = ParagraphStyle(
    name="Description",
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    spaceAfter=0,
    spaceBefore=0,
    alignment=TA_LEFT,
)

# ================= Main =================
def generate_invoice_pdf(invoice: Invoice, output_path: str) -> None:
    c = canvas.Canvas(output_path, pagesize=A4)
    y = PAGE_HEIGHT - TOP_MARGIN

    y = _draw_header(c, invoice, y)
    y -= 18

    y = _draw_parties(c, invoice, y)
    y -= 20

    y = _draw_line_items(c, invoice, y)

    totals_y = max(y - 20, TOTALS_MIN_Y)
    _draw_totals(c, invoice, totals_y)

    if invoice.notes:
        _draw_notes(c, invoice.notes, totals_y - 40)

    _draw_footer(c, invoice)

    c.showPage()
    c.save()


# ================= Header =================
def _draw_header(c, invoice: Invoice, y: float) -> float:
    header_top = y
    header_bottom = y - HEADER_HEIGHT
    center_y = (header_top + header_bottom) / 2

    logo_width = logo_height = 0

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
                center_y - logo_height / 2,
                width=logo_width,
                height=logo_height,
                mask="auto",
            )

    text_x = LEFT_MARGIN + logo_width + (8 if logo_width else 0)

    # Company name
    c.setFont("Helvetica-Bold", 16)
    c.drawString(text_x, center_y + 4, invoice.company.name)

    # Invoice meta (top-right, aligned)
    c.setFont("Helvetica", 10)
    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        center_y + 6,
        f"Invoice #{invoice.invoice_number}",
    )
    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        center_y - 6,
        f"Date: {invoice.invoice_date}",
    )

    return header_bottom

# ================= Parties =================
def _draw_parties(c, invoice: Invoice, y: float) -> float:
    left_x = LEFT_MARGIN
    right_x = PAGE_WIDTH / 2 + 10

    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_x, y, "Bill From")
    c.drawString(right_x, y, "Bill To")

    y -= LINE_HEIGHT + 4
    left_height = _draw_party_block(c, invoice.company, left_x, y)
    right_height = _draw_party_block(c, invoice.client, right_x, y)

    return y - max(left_height, right_height)


def _draw_party_block(c, party, x: float, y: float) -> float:
    c.setFont("Helvetica", 10)
    offset = 0

    c.drawString(x, y, party.name)
    offset += LINE_HEIGHT

    for line in party.address.split("\n"):
        c.drawString(x, y - offset, line)
        offset += LINE_HEIGHT

    if party.email:
        c.drawString(x, y - offset, party.email)
        offset += LINE_HEIGHT

    return offset


# ================= Line Items =================
def _draw_line_items(c, invoice: Invoice, y: float) -> float:
    def draw_header(y_pos):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(COL_DESC, y_pos, "Description")
        c.drawRightString(COL_QTY, y_pos, "Qty")
        c.drawRightString(COL_UNIT, y_pos, "Unit Price")
        c.drawRightString(COL_TOTAL, y_pos, "Amount")

        c.line(
            LEFT_MARGIN,
            y_pos - RULE_GAP,
            PAGE_WIDTH - RIGHT_MARGIN,
            y_pos - RULE_GAP,
        )

        return y_pos - LINE_HEIGHT - RULE_GAP

    y = draw_header(y)
    c.setFont("Helvetica", 10)

    for item in invoice.line_items:
        desc = Paragraph(item.description, DESC_STYLE)
        avail_width = COL_QTY - COL_DESC - 6
        w, h = desc.wrap(avail_width, PAGE_HEIGHT)

        row_height = max(h, LINE_HEIGHT) + ROW_PADDING

        if y - row_height < BOTTOM_MARGIN + 70:
            c.showPage()
            y = PAGE_HEIGHT - TOP_MARGIN
            y = _draw_header(c, invoice, y)
            y -= 18
            y = _draw_parties(c, invoice, y)
            y -= 20
            y = draw_header(y)

        desc.drawOn(c, COL_DESC, y - h + 4)

        c.drawRightString(COL_QTY, y, str(item.quantity))
        c.drawRightString(COL_UNIT, y, _fmt_money(item.unit_price))
        c.drawRightString(COL_TOTAL, y, _fmt_money(item.line_total))

        y -= row_height

    c.line(
        LEFT_MARGIN,
        y + RULE_GAP,
        PAGE_WIDTH - RIGHT_MARGIN,
        y + RULE_GAP,
    )

    return y

def _fmt_money(value: float) -> str:
    return f"{CURRENCY_SYMBOL}{value:,.2f}"


# ================= Totals =================
def _draw_totals(c, invoice: Invoice, y: float) -> None:
    label_x = COL_UNIT
    value_x = COL_TOTAL

    c.setFont("Helvetica", 10)
    c.drawRightString(label_x, y, "Subtotal")
    c.drawRightString(value_x, y, _fmt_money(invoice.subtotal))

    y -= LINE_HEIGHT
    tax_label = f"{invoice.tax_label} ({int(invoice.tax_rate*100)}%)"
    c.drawRightString(label_x, y, tax_label)
    c.drawRightString(value_x, y, _fmt_money(invoice.tax_amount))

    y -= LINE_HEIGHT + 6
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(label_x, y, "Total")
    c.drawRightString(value_x, y, _fmt_money(invoice.total))


# ================= Notes =================
def _draw_notes(c, notes: str, y: float) -> None:
    c.line(
        LEFT_MARGIN,
        y,
        PAGE_WIDTH - RIGHT_MARGIN,
        y
    )

    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT_MARGIN, y, "Notes")

    y -= LINE_HEIGHT
    c.setFont("Helvetica", 10)
    c.drawString(LEFT_MARGIN, y, notes)


# ================= Footer =================
def _draw_footer(c, invoice: Invoice) -> None:
    if not invoice.footer:
        return

    c.setFont("Helvetica", 8)
    c.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 8, invoice.footer)

