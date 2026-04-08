from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import os
import io

# ── Brand colours ──────────────────────────────────────────────
ORANGE  = colors.HexColor("#FF4B00")
BLACK   = colors.HexColor("#0A0A0A")
WHITE   = colors.white
GREY_BG = colors.HexColor("#1A1A1A")
GREY_LT = colors.HexColor("#2C2C2C")
DIVIDER = colors.HexColor("#333333")

# ── Page setup ─────────────────────────────────────────────────
PAGE_W, PAGE_H = A5
MARGIN = 14 * mm


def draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None):
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - r, y, x + w, y + r, -90, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - r, y + h - r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - r, x + r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + r, y + r, 180, 90)
    p.close()
    c.saveState()
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(0.5)
        c.drawPath(p, fill=1, stroke=1)
    else:
        c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def generate_receipt(
    name,
    phone,
    amount,
    plan,
    start_date,
    expiry_date,
    receipt_no=None,
    logo_path="logo.jpeg",
):
    """
    Generates a PDF receipt and returns (file_name, pdf_bytes).
    file_name  — suggested filename for saving/uploading
    pdf_bytes  — raw PDF bytes (ready to upload or download)
    """
    if receipt_no is None:
        receipt_no = f"O9W-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    file_name = f"receipt_{phone}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    # ── Draw into a BytesIO buffer ────────────────────────────────
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A5)
    c.setTitle(f"ONE9 Warriors Receipt - {name}")

    # Background
    c.setFillColor(BLACK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Header band
    header_h = 52 * mm
    c.setFillColor(GREY_BG)
    c.rect(0, PAGE_H - header_h, PAGE_W, header_h, fill=1, stroke=0)

    # Orange accent bar at top
    c.setFillColor(ORANGE)
    c.rect(0, PAGE_H - 2.5 * mm, PAGE_W, 2.5 * mm, fill=1, stroke=0)

    # Logo
    if os.path.exists(logo_path):
        logo_size = 28 * mm
        logo_x = MARGIN
        logo_y = PAGE_H - header_h + (header_h - logo_size) / 2
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, logo_x, logo_y, width=logo_size, height=logo_size,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    # Club name & tagline
    text_x = MARGIN + 33 * mm
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(text_x, PAGE_H - 20 * mm, "ONE9 WARRIOR'S")

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(text_x + 1, PAGE_H - 27 * mm, "T H E   F I G H T   C L U B")

    c.setFillColor(DIVIDER)
    c.setLineWidth(0.4)
    c.line(MARGIN, PAGE_H - header_h + 8 * mm, PAGE_W - MARGIN, PAGE_H - header_h + 8 * mm)

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 6.5)
    c.drawString(text_x + 1, PAGE_H - header_h + 11 * mm, "MEMBERSHIP RECEIPT")

    # Receipt number & date
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7)
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - header_h + 11 * mm, date_str)

    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 7)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - header_h + 4 * mm, f"# {receipt_no}")

    # Amount card
    card_y = PAGE_H - header_h - 36 * mm
    draw_rounded_rect(c, MARGIN, card_y, PAGE_W - 2 * MARGIN, 28 * mm, 4 * mm, GREY_LT)
    draw_rounded_rect(c, MARGIN, card_y, 4 * mm, 28 * mm, 2 * mm, ORANGE)

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN + 9 * mm, card_y + 19 * mm, "AMOUNT PAID")

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(MARGIN + 9 * mm, card_y + 8 * mm, f"Rs.{amount}")

    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(PAGE_W - MARGIN - 6 * mm, card_y + 13 * mm, str(plan).upper())

    c.setFillColor(colors.HexColor("#666666"))
    c.setFont("Helvetica", 7)
    c.drawRightString(PAGE_W - MARGIN - 6 * mm, card_y + 7 * mm, "MEMBERSHIP PLAN")

    # Member details
    def detail_row(label, value, y_pos):
        c.setFillColor(colors.HexColor("#666666"))
        c.setFont("Helvetica", 7.5)
        c.drawString(MARGIN, y_pos, label.upper())
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, y_pos - 5.5 * mm, str(value))
        c.setStrokeColor(DIVIDER)
        c.setLineWidth(0.3)
        c.line(MARGIN, y_pos - 7.5 * mm, PAGE_W - MARGIN, y_pos - 7.5 * mm)

    section_label_y = card_y - 10 * mm
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, section_label_y, "MEMBER DETAILS")

    row_start = section_label_y - 8 * mm
    row_gap   = 14 * mm

    detail_row("Member Name", name,        row_start)
    detail_row("Phone",       phone,       row_start - row_gap)
    detail_row("Start Date",  start_date,  row_start - 2 * row_gap)
    detail_row("Expiry Date", expiry_date, row_start - 3 * row_gap)

    # Footer
    footer_y = 9 * mm
    c.setFillColor(GREY_BG)
    c.rect(0, 0, PAGE_W, footer_y + 3 * mm, fill=1, stroke=0)

    c.setFillColor(ORANGE)
    c.rect(0, 0, PAGE_W, 1.5 * mm, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(PAGE_W / 2, footer_y, "Thank you for being a ONE9 Warrior!")
    c.drawCentredString(PAGE_W / 2, footer_y - 4 * mm,
                        "This is a computer-generated receipt and requires no signature.")

    c.save()

    # Return filename + raw bytes
    pdf_bytes = buffer.getvalue()
    return file_name, pdf_bytes