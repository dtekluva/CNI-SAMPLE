"""
Immutable minutes PDF (FR-MIN-3). Renders the sealed minutes with the agenda-
linked narrative, attendee list, signature block and content hash so the export
is a self-contained statutory record.
"""
import io
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def render_minutes_pdf(*, minutes, watermark=""):
    meeting = minutes.meeting
    entity = meeting.entity
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    width, height = A4
    left = 56
    y = height - 60

    def line(text, font="Helvetica", size=11, gap=16, gray=0):
        nonlocal y
        if y < 70:
            _footer(c, minutes, watermark, width)
            c.showPage()
            y = height - 60
        c.setFont(font, size)
        c.setFillGray(gray)
        c.drawString(left, y, text)
        y -= gap

    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0.45)
    c.drawString(left, y, entity.legal_name.upper())
    y -= 22
    line(f"Minutes — {meeting.title}", "Helvetica-Bold", 17, 22)
    line(meeting.starts_at.strftime("%d %B %Y, %H:%M"), "Helvetica", 11, 20, gray=0.4)

    attendees = list(minutes.attendees.all())
    if attendees:
        line("Present", "Helvetica-Bold", 11, 16)
        for a in attendees:
            line(f"  • {a.name or a.email}", "Helvetica", 10, 14, gray=0.2)
        y -= 6

    for b in minutes.blocks.select_related("agenda_item").order_by("agenda_item__position", "id"):
        line(f"{b.agenda_item.position}. {b.agenda_item.title}", "Helvetica-Bold", 12, 18)
        body = b.text or "(No minute recorded.)"
        for para in body.split("\n"):
            for wrapped in (textwrap.wrap(para, width=92) or [""]):
                line(wrapped, "Helvetica", 10.5, 14, gray=0.1)
        y -= 8

    # Signature / seal block
    y -= 10
    c.setStrokeGray(0.8)
    c.line(left, y, width - 56, y)
    y -= 20
    if minutes.signed_by_id and minutes.signed_at:
        line(f"Signed by {minutes.signed_by.name or minutes.signed_by.email}", "Helvetica-Bold", 11, 16)
        line(minutes.signed_at.strftime("Signed %d %B %Y at %H:%M"), "Helvetica", 10, 16, gray=0.35)
    line(f"Content hash (SHA-256): {minutes.content_hash or '—'}", "Helvetica", 8, 14, gray=0.4)
    _footer(c, minutes, watermark, width)
    c.save()
    return buf.getvalue()


def _footer(c, minutes, watermark, width):
    c.setFont("Helvetica", 7)
    c.setFillGray(0.55)
    stamp = watermark or f"{minutes.meeting.entity.legal_name} — statutory minute book"
    c.drawString(56, 24, stamp)
    if minutes.state == minutes.State.SIGNED:
        c.drawRightString(width - 56, 24, "SEALED / IMMUTABLE")
