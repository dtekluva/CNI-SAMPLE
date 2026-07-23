from django.db.models import Max

from apps.audit.models import AuditEvent

from .models import BoardPack, Document


def build_toc(meeting):
    """Compute the ToC (item -> start page) without creating a pack version."""
    toc = []
    cursor = 2  # page 1 is the cover
    for i, item in enumerate(meeting.agenda_items.all()):
        papers = list(Document.objects.filter(agenda_item=item))
        toc.append(
            {
                "number": i + 1,
                "item_id": item.id,
                "title": item.title,
                "page": cursor,
                "papers": [
                    {"title": p.title, "pages": p.page_count, "late": p.is_late} for p in papers
                ],
            }
        )
        cursor += sum(p.page_count for p in papers)
    return toc, max(cursor - 1, 1)


def compile_pack(*, meeting, actor):
    """
    Compile a versioned board pack (FR-MTG-4): cover page + agenda papers, with an
    auto table of contents mapping each item to its start page. Republishing
    increments the version and records a 'pack.republished' notice.
    """
    last = meeting.board_packs.aggregate(m=Max("version_number"))["m"] or 0
    version = last + 1
    pack = BoardPack.objects.create(meeting=meeting, version_number=version, published_by=actor)
    toc, total_pages = build_toc(meeting)

    action = "pack.republished" if version > 1 else "pack.published"
    AuditEvent.objects.record(action=action, actor=actor, target=meeting, metadata={"version": version})
    return {"pack": pack, "toc": toc, "total_pages": total_pages}
