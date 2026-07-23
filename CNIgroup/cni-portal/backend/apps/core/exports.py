"""
Regulator-ready exports (FR-RPT-3): one-click, dated, entity-branded PDFs of
the statutory records — minute book, resolution register, attendance register,
and an audit-log extract.
"""
import io

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

MARGIN = 56


def _header(c, entity, title, user):
    width, height = A4
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0.45)
    c.drawString(MARGIN, height - 46, entity.legal_name.upper())
    if entity.cac_rc_number:
        c.drawRightString(width - MARGIN, height - 46, f"RC {entity.cac_rc_number}")
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(MARGIN, height - 76, title)
    c.setFont("Helvetica", 9)
    c.setFillGray(0.4)
    who = user.name or user.email
    c.drawString(MARGIN, height - 94, f"Generated {timezone.now():%d %B %Y %H:%M} by {who} — statutory record extract")
    c.setFillGray(0)
    c.setStrokeGray(0.85)
    c.line(MARGIN, height - 106, width - MARGIN, height - 106)
    return height - 132


def _line(c, y, text, size=10, bold=False, gray=0.0):
    width, height = A4
    if y < 64:
        c.showPage()
        y = height - 64
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillGray(gray)
    c.drawString(MARGIN, y, text[:110])
    c.setFillGray(0)
    return y - (size + 6)


def render_minute_book(entity, user):
    from apps.minutes.models import Minutes

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    y = _header(c, entity, "Minute Book", user)
    entries = Minutes.objects.filter(meeting__entity=entity, state=Minutes.State.SIGNED).select_related("meeting")
    if not entries:
        y = _line(c, y, "No signed minutes on record.", gray=0.4)
    for m in entries:
        y = _line(c, y, f"{m.meeting.title} — held {m.meeting.starts_at:%d %B %Y}", size=12, bold=True)
        y = _line(c, y, f"Seal: {m.content_hash[:32]}…  ·  signed {m.signed_at:%d %b %Y}" if m.content_hash and m.signed_at else "Sealed", size=9, gray=0.4)
        for b in m.blocks.select_related("agenda_item"):
            if b.text:
                y = _line(c, y, f"  {b.agenda_item.title}: {b.text[:100]}", size=9, gray=0.2)
        y -= 8
    c.save()
    return buf.getvalue()


def render_resolution_register(entity, user):
    from apps.resolutions.models import Resolution

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    y = _header(c, entity, "Resolution Register", user)
    for r in Resolution.objects.filter(entity=entity).order_by("year", "number"):
        y = _line(c, y, f"{r.number}  ·  {r.title}", size=11, bold=True)
        y = _line(c, y, f"  {r.get_kind_display()} · {r.get_resolution_class_display()} · outcome: {r.outcome}"
                        + (f" · effective {r.effective_date:%d %b %Y}" if r.effective_date else ""), size=9, gray=0.35)
        y -= 4
    c.save()
    return buf.getvalue()


def render_attendance_register(entity, user):
    from apps.meetings.models import Meeting

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    y = _header(c, entity, "Attendance Register", user)
    for m in Meeting.objects.filter(entity=entity).order_by("starts_at"):
        y = _line(c, y, f"{m.title} — {m.starts_at:%d %B %Y}", size=11, bold=True)
        for a in m.attendances.select_related("member"):
            who = a.member.name or a.member.email
            y = _line(c, y, f"  {who}: {a.get_status_display()} ({a.get_mode_display()})", size=9, gray=0.3)
        y -= 6
    c.save()
    return buf.getvalue()


def render_audit_extract(entity, user):
    from apps.audit.models import AuditEvent

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    y = _header(c, entity, "Audit Log Extract (latest 300)", user)
    for e in AuditEvent.objects.order_by("-id")[:300]:
        actor = e.actor.email if e.actor_id else "system"
        y = _line(c, y, f"{e.timestamp:%d %b %Y %H:%M:%S}  {e.action}  ·  {actor}", size=8, gray=0.25)
    c.save()
    return buf.getvalue()


RENDERERS = {
    "minute-book": render_minute_book,
    "resolution-register": render_resolution_register,
    "attendance-register": render_attendance_register,
    "audit-extract": render_audit_extract,
}
