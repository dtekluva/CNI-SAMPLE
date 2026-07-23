"""
PDF rendering for board packs and CTCs (FR-MTG-4, FR-RES-4).
Every page carries the per-viewer watermark (FR-DOC-3).
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .packs import build_toc


def _stamp(c, watermark, width):
    if not watermark:
        return
    c.saveState()
    c.setFont("Helvetica", 7)
    c.setFillGray(0.5)
    c.drawString(56, 24, watermark)  # footer watermark on every page
    c.restoreState()


def render_pack_pdf(*, meeting, watermark=""):
    toc, _total = build_toc(meeting)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    width, height = A4

    # Cover
    c.setFont("Helvetica-Bold", 20)
    c.drawString(56, height - 120, meeting.entity.legal_name)
    c.setFont("Helvetica", 15)
    c.drawString(56, height - 150, f"Board Pack — {meeting.title}")
    c.drawString(56, height - 172, meeting.starts_at.strftime("%d %B %Y"))
    _stamp(c, watermark, width)
    c.showPage()

    # Table of contents
    c.setFont("Helvetica-Bold", 16)
    c.drawString(56, height - 90, "Table of Contents")
    c.setFont("Helvetica", 12)
    y = height - 128
    for item in toc:
        c.drawString(56, y, f"{item['number']}. {item['title']}")
        c.drawRightString(width - 56, y, str(item["page"]))
        y -= 20
    _stamp(c, watermark, width)
    c.showPage()

    c.save()
    return buf.getvalue()


def render_ctc_pdf(*, ctc):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    width, height = A4
    text = c.beginText(56, height - 90)
    text.setFont("Helvetica", 11)
    for line in ctc.body.splitlines():
        text.textLine(line)
    c.drawText(text)
    _stamp(c, f"CTC {ctc.reference}", width)
    c.showPage()
    c.save()
    return buf.getvalue()


def render_document_pdf(*, document, watermark=""):
    """Render a document's latest version as a watermarked PDF (FR-DOC-3)."""
    import textwrap

    latest = document.versions.first()
    text = (latest.text_content if latest else "") or "(No content in this version.)"

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    width, height = A4

    # Header block
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0.45)
    c.drawString(56, height - 50, document.entity.legal_name.upper())
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(56, height - 84, document.title[:70])
    c.setFont("Helvetica", 10)
    c.setFillGray(0.4)
    meta = f"Version {latest.version_number if latest else '—'} · {document.page_count} pp"
    if document.topic:
        meta += f" · {document.topic}"
    c.drawString(56, height - 104, meta)
    c.setFillGray(0)
    c.setStrokeGray(0.85)
    c.line(56, height - 118, width - 56, height - 118)

    # Flowing body
    y = height - 148
    c.setFont("Helvetica", 11)
    for para in text.split("\n"):
        lines = textwrap.wrap(para, width=88) or [""]
        for line in lines:
            if y < 64:
                _stamp(c, watermark, width)
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 64
            c.drawString(56, y, line)
            y -= 16
        y -= 6  # paragraph gap
    _stamp(c, watermark, width)
    c.save()
    return buf.getvalue()
