from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os


def generate_invoice_pdf(invoice: dict, output_path: str) -> None:
    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    margin_x = 20 * mm
    y = page_height - 20 * mm

    _draw_header(c, invoice, margin_x, y)
    y -= 40 * mm

    _draw_parties(c, invoice, margin_x, y)
    y -= 35 * mm

    _draw_line_items(c, invoice, margin_x, y)
    y -= (len(invoice["line_items"]) + 2) * 10 * mm

    _draw_totals(c, invoice, margin_x, y)
    y -= 25 * mm

    if invoice.get("notes"):
        _draw_notes(c, invoice["notes"], margin_x, y)

    c.showPage()
    c.save()


def _draw_header(c, invoice: dict, x: float, y: float) -> None:
    company = invoice["company"]

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, company["name"])

    logo_path = company.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            x + 120 * mm,
            y - 10 * mm,
            width=40 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    c.setFont("Helvetica", 10)
    c.drawRightString(
        x + 170 * mm,
        y,
        f"Invoice: {invoice['invoice_number']}",
    )
    c.drawRightString(
        x + 170 * mm,
        y - 12,
        f"Date: {invoice['invoice_date']}",
    )


def _draw_parties(c, invoice: dict, x: float, y: float) -> None:
    company = invoice["company"]
    client = invoice["client"]

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Bill From:")
    c.drawString(x + 90 * mm, y, "Bill To:")

    c.setFont("Helvetica", 10)
    _draw_party_block(c, company, x, y - 12)
    _draw_party_block(c, client, x + 90 * mm, y - 12)


def _draw_party_block(c, party: dict, x: float, y: float) -> None:
    c.drawString(x, y, party["name"])

    # Split address by newline and draw each line
    for i, line in enumerate(party["address"].split("\n")):
        c.drawString(x, y - 12 * (i + 1), line)

    c.drawString(x, y - 12 * (len(party["address"].split("\n")) + 1), party["email"])


def _draw_line_items(c, invoice: dict, x: float, y: float) -> None:
    c.setFont("Helvetica-Bold", 10)

    c.drawString(x, y, "Description")
    c.drawRightString(x + 110 * mm, y, "Qty")
    c.drawRightString(x + 140 * mm, y, "Unit Price")
    c.drawRightString(x + 170 * mm, y, "Line Total")

    c.setFont("Helvetica", 10)
    y -= 12

    for item in invoice["line_items"]:
        c.drawString(x, y, item["description"])
        c.drawRightString(x + 110 * mm, y, f"{item['quantity']}")
        c.drawRightString(x + 140 * mm, y, f"{item['unit_price']:.2f}")
        c.drawRightString(x + 170 * mm, y, f"{item['line_total']:.2f}")
        y -= 12


def _draw_totals(c, invoice: dict, x: float, y: float) -> None:
    c.setFont("Helvetica", 10)

    c.drawRightString(x + 140 * mm, y, "Subtotal:")
    c.drawRightString(x + 170 * mm, y, f"{invoice['subtotal']:.2f}")

    c.drawRightString(x + 140 * mm, y - 12, "Tax:")
    c.drawRightString(x + 170 * mm, y - 12, f"{invoice['tax_amount']:.2f}")

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(x + 140 * mm, y - 26, "Total:")
    c.drawRightString(x + 170 * mm, y - 26, f"{invoice['total']:.2f}")


def _draw_notes(c, notes: str, x: float, y: float) -> None:
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, "Notes")

    c.setFont("Helvetica", 10)
    c.drawString(x, y - 12, notes)
