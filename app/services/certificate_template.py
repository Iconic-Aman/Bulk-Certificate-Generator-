import math
import re
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = landscape(A4)  # 841.89 x 595.27 pt

NAVY = HexColor("#14284B")
GOLD = HexColor("#B8923A")
GOLD_LIGHT = HexColor("#E3C77A")
CREAM = HexColor("#FFFDF6")
GREY = HexColor("#555555")

ORG_NAME = "Your Organization Name"
TITLE = "CERTIFICATE"
SUBTITLE = "OF COMPLETION"


def _safe_text(value, default=""):
    """Strip control characters; keep text printable for the built-in fonts."""
    if value is None:
        return default
    return re.sub(r"[\x00-\x1f\x7f]", "", str(value)).strip()


def _fit_font_size(text, font, max_size, max_width, min_size=14):
    """Shrink font until text fits; raise if it cannot fit (caller marks item failed)."""
    size = max_size
    while size >= min_size:
        if stringWidth(text, font, size) <= max_width:
            return size
        size -= 1
    raise ValueError("Text is too long to fit on the certificate")


def _draw_corner(c, x, y, sx, sy):
    """Simple ornamental corner flourish. sx/sy = +1/-1 mirror the shape."""
    c.saveState()
    c.translate(x, y)
    c.scale(sx, sy)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.6)
    c.line(0, 0, 70, 0)
    c.line(0, 0, 0, 70)
    c.setLineWidth(0.8)
    c.line(8, 8, 52, 8)
    c.line(8, 8, 8, 52)
    c.setFillColor(GOLD)
    c.circle(0, 0, 4, stroke=0, fill=1)
    c.circle(70, 0, 2.5, stroke=0, fill=1)
    c.circle(0, 70, 2.5, stroke=0, fill=1)
    c.restoreState()


def _draw_seal(c, cx, cy, r=42):
    """Gold rosette seal with two ribbon tails."""
    # ribbons
    c.setFillColor(NAVY)
    for dx in (-14, 14):
        p = c.beginPath()
        p.moveTo(cx + dx - 11, cy - 10)
        p.lineTo(cx + dx + 11, cy - 10)
        p.lineTo(cx + dx + 11 + (6 if dx > 0 else -6), cy - r - 22)
        p.lineTo(cx + dx, cy - r - 12)
        p.lineTo(cx + dx - 11 + (6 if dx > 0 else -6), cy - r - 22)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    # scalloped edge
    c.setFillColor(GOLD)
    n = 28
    for i in range(n):
        a = 2 * math.pi * i / n
        c.circle(cx + (r) * math.cos(a), cy + (r) * math.sin(a), 6, stroke=0, fill=1)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(GOLD_LIGHT)
    c.circle(cx, cy, r - 7, stroke=0, fill=1)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.circle(cx, cy, r - 12, stroke=1, fill=0)
    # star
    c.setFillColor(NAVY)
    p = c.beginPath()
    pts = []
    for i in range(10):
        rad = (r - 18) if i % 2 == 0 else (r - 18) * 0.45
        a = math.pi / 2 + i * math.pi / 5
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def _draw_diamond_divider(c, cx, y, half=110):
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(cx - half, y, cx - 10, y)
    c.line(cx + 10, y, cx + half, y)
    c.setFillColor(GOLD)
    p = c.beginPath()
    p.moveTo(cx, y + 5)
    p.lineTo(cx + 6, y)
    p.lineTo(cx, y - 5)
    p.lineTo(cx - 6, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def draw_certificate(c, name=None, course="Course / Event Name",
                     date=None, certificate_id=None,
                     issuer=ORG_NAME, signatory="Authorized Signatory"):
    """Draw one certificate page on an existing canvas."""
    name = _safe_text(name)
    course = _safe_text(course, "Course / Event Name")
    date = _safe_text(date)
    certificate_id = _safe_text(certificate_id)
    cx = PAGE_W / 2

    # --- background + borders -------------------------------------------
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    c.setStrokeColor(NAVY)
    c.setLineWidth(10)
    c.rect(22, 22, PAGE_W - 44, PAGE_H - 44, stroke=1, fill=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.5)
    c.rect(36, 36, PAGE_W - 72, PAGE_H - 72, stroke=1, fill=0)
    c.setLineWidth(0.8)
    c.rect(44, 44, PAGE_W - 88, PAGE_H - 88, stroke=1, fill=0)

    _draw_corner(c, 52, 52, 1, 1)
    _draw_corner(c, PAGE_W - 52, 52, -1, 1)
    _draw_corner(c, 52, PAGE_H - 52, 1, -1)
    _draw_corner(c, PAGE_W - 52, PAGE_H - 52, -1, -1)

    # --- heading ----------------------------------------------------------
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx, PAGE_H - 85, issuer.upper())

    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 52)
    c.drawCentredString(cx, PAGE_H - 140, TITLE)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(cx, PAGE_H - 166, "   ".join(SUBTITLE))
    _draw_diamond_divider(c, cx, PAGE_H - 186)

    # --- presented to -----------------------------------------------------
    c.setFillColor(GREY)
    c.setFont("Times-Italic", 17)
    c.drawCentredString(cx, PAGE_H - 220, "This certificate is proudly presented to")

    # --- NAME AREA (line to write on / name printed above it) -------------
    name_line_y = PAGE_H - 282
    line_half = 250
    if name:
        max_w = 2 * line_half - 20
        size = _fit_font_size(name, "Times-BoldItalic", 38, max_w)
        c.setFillColor(NAVY)
        c.setFont("Times-BoldItalic", size)
        c.drawCentredString(cx, name_line_y + 8, name)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    c.line(cx - line_half, name_line_y, cx + line_half, name_line_y)
    c.setFillColor(GREY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx, name_line_y - 12, "RECIPIENT NAME")

    # --- description ------------------------------------------------------
    c.setFillColor(GREY)
    c.setFont("Times-Italic", 16)
    c.drawCentredString(cx, name_line_y - 45, "for successfully completing")
    course_size = _fit_font_size(course, "Times-Bold", 24, PAGE_W - 220)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", course_size)
    c.drawCentredString(cx, name_line_y - 76, course)

    # --- seal (centre bottom) ---------------------------------------------
    _draw_seal(c, cx, 138)

    # --- signature + date lines -------------------------------------------
    base_y = 105
    left_x, right_x = 150, PAGE_W - 150
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    for x in (left_x, right_x):
        c.line(x - 85, base_y, x + 85, base_y)

    if date:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(left_x, base_y + 6, date)
    c.setFillColor(GREY)
    c.setFont("Helvetica", 10)
    c.drawCentredString(left_x, base_y - 14, "DATE")
    c.drawCentredString(right_x, base_y - 14, signatory.upper())

    # --- certificate id ---------------------------------------------------
    if certificate_id:
        c.setFillColor(GREY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx, 54, f"Certificate ID: {certificate_id}")


def generate_certificate(path, name=None, course="Course / Event Name",
                         date=None, certificate_id=None, **kwargs):
    """Create a single-page PDF certificate at `path`.

    Raises ValueError if the name/course cannot fit (caller should mark
    that recipient as failed and continue with the others).
    """
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Certificate")
    c.setAuthor(ORG_NAME)
    draw_certificate(c, name=name, course=course, date=date,
                     certificate_id=certificate_id, **kwargs)
    c.showPage()
    c.save()
    return str(path)


if __name__ == "__main__":
    generate_certificate("certificate_blank.pdf", course="Python Backend Development",
                         date=None, certificate_id=None)
    generate_certificate("certificate_sample.pdf", name="Rahul Sharma",
                         course="Python Backend Development",
                         date="07 October 2026", certificate_id="CERT-2026-0001")
    print("Created certificate_blank.pdf and certificate_sample.pdf")