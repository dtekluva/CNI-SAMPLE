from .models import Attendance


def check_in(*, meeting, member, mode=Attendance.Mode.PHYSICAL, status=Attendance.Status.PRESENT, proxy_for=None):
    attendance, _ = Attendance.objects.update_or_create(
        meeting=meeting,
        member=member,
        defaults={"mode": mode, "status": status, "proxy_for": proxy_for},
    )
    return attendance


def record_apology(*, meeting, member):
    return check_in(meeting=meeting, member=member, status=Attendance.Status.APOLOGY)


def quorum_status(meeting):
    """Live quorum indicator (FR-MTG-5)."""
    present = meeting.attendances.filter(status=Attendance.Status.PRESENT).count()
    return {
        "present": present,
        "quorum": meeting.quorum,
        "met": meeting.quorum > 0 and present >= meeting.quorum,
    }


def attendance_stats(member):
    """Per-director attendance statistics (feeds evaluations / annual report)."""
    qs = Attendance.objects.filter(member=member)
    return {
        "meetings": qs.count(),
        "present": qs.filter(status=Attendance.Status.PRESENT).count(),
        "apologies": qs.filter(status=Attendance.Status.APOLOGY).count(),
    }
