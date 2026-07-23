"""
Seed the platform with realistic demo data across every domain, so each screen
has something to show (entities, roles, meetings, agenda, attendance, documents,
packs, minutes, resolutions, votes, signatures, CTCs, actions, notifications,
statutory registers, audit trail).

Idempotent: safe to re-run (get_or_create keyed on natural identifiers).
Passwords are only set for accounts this command CREATES — an existing account
(e.g. the real cosec login) keeps its password untouched.
"""
import hashlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.actions.models import Action
from apps.audit.models import AuditEvent
from apps.documents.models import BoardPack, Document, DocumentVersion
from apps.entities.models import Entity, EntitySettings
from apps.meetings.models import AgendaItem, Attendance, Meeting
from apps.minutes.models import InlineDecision, MinuteBlock, MinuteComment, Minutes
from apps.notifications.models import Notification
from apps.rbac.models import Role
from apps.rbac.services import assign_role
from apps.registers.models import RegisterEntry, RegisterType
from apps.resolutions.models import CertifiedTrueCopy, Resolution, Signature, Vote

User = get_user_model()

DEMO_PASSWORD = "CniDemo-2026!"
COSEC_EMAIL = "admin@group.com"


class Command(BaseCommand):
    help = "Populate the whole platform with demo governance data (idempotent)."

    def handle(self, *args, **options):
        now = timezone.now()
        out = self.stdout.write

        # ---------- users ----------
        def user(email, name, **extra):
            u, created = User.objects.get_or_create(email=email, defaults={"name": name, **extra})
            if created:
                u.set_password(DEMO_PASSWORD)
                u.save()
            elif not u.name:
                u.name = name
                u.save(update_fields=["name"])
            return u

        cosec = user(COSEC_EMAIL, "Alexa Moore", is_staff=True, is_superuser=True)
        if not (cosec.is_staff and cosec.is_superuser):  # pre-existing account: grant admin too
            cosec.is_staff = cosec.is_superuser = True
            cosec.save(update_fields=["is_staff", "is_superuser"])
        chairman = user("chairman@cnigroup.demo", "Chief Adaeze Okonkwo")
        md = user("md@cnigroup.demo", "Emeka Nwachukwu")
        dir1 = user("f.balogun@cnigroup.demo", "Folake Balogun")
        dir2 = user("t.danjuma@cnigroup.demo", "Talatu Danjuma")
        dir3 = user("k.eze@cnigroup.demo", "Kelechi Eze")
        dir4 = user("a.suleiman@cnigroup.demo", "Amina Suleiman")
        auditor = user("auditor@cnigroup.demo", "Olu Fashola (KPMG)")
        board = [chairman, md, dir1, dir2, dir3, dir4]

        # ---------- entities ----------
        def entity(name, code, parent=None, rc="", inc=None):
            e, _ = Entity.objects.get_or_create(
                legal_name=name,
                defaults=dict(
                    parent=parent,
                    code=code,
                    cac_rc_number=rc,
                    incorporation_date=inc,
                    registered_address="14 Adeola Odeku Street, Victoria Island, Lagos",
                    share_capital=100_000_000,
                    financial_year_end="12-31",
                    company_secretary="Inyang Inyangete",
                    auditors="KPMG Professional Services",
                    regulators=["CAC", "FIRS"],
                ),
            )
            EntitySettings.objects.get_or_create(entity=e)
            return e

        holdco = entity("C&I Leasing Plc", "CIL", rc="RC1482203", inc=now.date() - timedelta(days=3650))
        libertypay = entity("Liberty Pay Limited", "LP", parent=holdco, rc="RC1523991", inc=now.date() - timedelta(days=2900))
        assured = entity("Liberty Assured Limited", "LA", parent=holdco, rc="RC1601246", inc=now.date() - timedelta(days=2500))
        props = entity("CNI Properties Limited", "CP", parent=holdco, rc="RC1688412", inc=now.date() - timedelta(days=1800))
        libertypay.regulators = ["CAC", "FIRS", "CBN"]
        libertypay.save(update_fields=["regulators"])

        # ---------- roles ----------
        assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
        assign_role(actor=cosec, user=chairman, role=Role.CHAIRMAN, entity=holdco)
        assign_role(actor=cosec, user=md, role=Role.EXECUTIVE_DIRECTOR, entity=holdco)
        assign_role(actor=cosec, user=dir1, role=Role.NON_EXECUTIVE_DIRECTOR, entity=holdco)
        assign_role(actor=cosec, user=dir2, role=Role.INDEPENDENT_DIRECTOR, entity=holdco)
        assign_role(actor=cosec, user=dir3, role=Role.NON_EXECUTIVE_DIRECTOR, entity=libertypay)
        assign_role(actor=cosec, user=dir4, role=Role.NON_EXECUTIVE_DIRECTOR, entity=assured)
        assign_role(actor=cosec, user=auditor, role=Role.AUDITOR, entity=holdco)

        # ---------- meetings ----------
        def meeting(e, title, when, mtype=Meeting.Type.BOARD, quorum=3, **extra):
            extra.setdefault("location", "Boardroom, 14 Adeola Odeku Street, VI, Lagos")
            m, _ = Meeting.objects.get_or_create(
                entity=e, title=title,
                defaults=dict(meeting_type=mtype, starts_at=when, quorum=quorum, **extra),
            )
            return m

        q1 = meeting(holdco, "Q1 2026 Board Meeting", now - timedelta(days=100))
        q2 = meeting(holdco, "Q2 2026 Board Meeting", now - timedelta(days=14))
        q3 = meeting(holdco, "Q3 2026 Board Meeting", now + timedelta(days=21),
                     is_virtual=True, virtual_link="https://meet.cnigroup.example/q3-board")
        Meeting.objects.filter(pk=q3.pk).update(
            virtual_provider="Microsoft Teams", dial_in="+234 1 448 5000 · ID 921 4477")
        lp_brd = meeting(libertypay, "Liberty Pay Board Meeting — H1 Review", now - timedelta(days=30))
        audit_cmte = meeting(holdco, "Audit Committee — Q2 Session", now - timedelta(days=20),
                             mtype=Meeting.Type.COMMITTEE, quorum=2)
        # further upcoming meetings so the calendar and dashboard have depth
        risk_cmte = meeting(holdco, "Board Risk Committee — Q3 Session", now + timedelta(days=9),
                            mtype=Meeting.Type.COMMITTEE, quorum=2)
        lp_q3 = meeting(libertypay, "Liberty Pay Board Meeting — Q3", now + timedelta(days=34),
                        is_virtual=True, virtual_link="https://meet.cnigroup.example/lp-q3")
        Meeting.objects.filter(pk=lp_q3.pk).update(
            virtual_provider="Zoom", dial_in="+234 1 448 5010 · ID 553 8821")
        agm = meeting(holdco, "2026 Annual General Meeting", now + timedelta(days=58),
                      mtype=Meeting.Type.AGM, quorum=5,
                      location="Eko Hotel & Suites, Victoria Island, Lagos")

        AGENDAS = {
            q1: [("Opening & apologies", "noting"), ("Minutes of previous meeting", "approval"),
                 ("Q4 2025 financial performance", "discussion"), ("2026 budget approval", "approval"),
                 ("Dividend recommendation", "approval"), ("AOB", "discussion")],
            q2: [("Opening & apologies", "noting"), ("Minutes of Q1 meeting", "approval"),
                 ("Q1 2026 financial performance", "discussion"), ("Liberty Pay CBN licence renewal", "discussion"),
                 ("Group risk register review", "discussion"), ("AOB", "discussion")],
            q3: [("Opening & apologies", "noting"), ("Minutes of Q2 meeting", "approval"),
                 ("H1 2026 group performance", "discussion"), ("CNI Properties land acquisition", "approval"),
                 ("2027 strategy kickoff", "discussion")],
            lp_brd: [("Opening", "noting"), ("H1 processing volumes", "discussion"),
                     ("Agent-network expansion", "approval"), ("Fraud & chargeback report", "discussion")],
            audit_cmte: [("External audit plan", "discussion"), ("Internal-controls report", "noting"),
                         ("Whistle-blowing log", "noting")],
            risk_cmte: [("Top risks review", "discussion"), ("FX exposure & hedging policy", "approval"),
                        ("Vendor concentration mitigation", "discussion")],
            lp_q3: [("Opening", "noting"), ("Q3 processing volumes", "discussion"),
                    ("CBN licence renewal status", "discussion"), ("Settlement partner mandate", "approval")],
            agm: [("Notice & quorum", "noting"), ("Audited financial statements", "approval"),
                  ("Declaration of dividend", "approval"), ("Re-election of directors", "approval"),
                  ("Appointment of auditors & remuneration", "approval")],
        }
        agenda_ix = {}
        for m, items in AGENDAS.items():
            for i, (title, itype) in enumerate(items, start=1):
                item, _ = AgendaItem.objects.get_or_create(
                    meeting=m, title=title,
                    defaults=dict(item_type=itype, position=i, owner=cosec, time_allocation_minutes=15),
                )
                agenda_ix[(m.pk, title)] = item

        # attendance for held meetings
        for m in (q1, q2, lp_brd, audit_cmte):
            for i, member in enumerate(board):
                status = Attendance.Status.APOLOGY if (m is q2 and member is dir2) else Attendance.Status.PRESENT
                mode = Attendance.Mode.VIRTUAL if i % 3 == 2 else Attendance.Mode.PHYSICAL
                Attendance.objects.get_or_create(meeting=m, member=member, defaults=dict(mode=mode, status=status))

        # ---------- documents & packs ----------
        def doc(e, title, m=None, item_title=None, pages=12, topic="", committee="", late=False,
                text="", downloadable=False):
            d, _ = Document.objects.get_or_create(
                entity=e, title=title,
                defaults=dict(
                    meeting=m,
                    access_mode=Document.AccessMode.DOWNLOADABLE if downloadable else Document.AccessMode.VIEW_ONLY,
                    page_count=pages, topic=topic, committee=committee, is_late=late,
                    agenda_item=agenda_ix.get((m.pk, item_title)) if (m and item_title) else None,
                ),
            )
            # update_or_create so re-seeding enriches existing rows with fuller content
            DocumentVersion.objects.update_or_create(
                document=d, version_number=1,
                defaults=dict(content_hash=hashlib.sha256(title.encode()).hexdigest(),
                              storage_key=f"demo/{e.code}/{title[:40]}.pdf",
                              text_content=text or f"{title} — demo paper for {e.legal_name}.",
                              uploaded_by=cosec),
            )
            return d

        SAMPLE_MINUTES = """MINUTES OF THE Q1 2026 MEETING OF THE BOARD OF DIRECTORS
C&I LEASING PLC (RC 1482203)
Held at the Boardroom, 14 Adeola Odeku Street, Victoria Island, Lagos

PRESENT: Chief Adaeze Okonkwo (Chairman), Emeka Nwachukwu (Managing Director), Folake Balogun (NED), Talatu Danjuma (Independent Director), Kelechi Eze (NED), Amina Suleiman (NED)
IN ATTENDANCE: Inyang Inyangete (Group Company Secretary), Olu Fashola (KPMG, for item 3)

1. OPENING & APOLOGIES
The Chairman opened the meeting at 10:02 and confirmed that due notice had been given under the Articles and that a quorum was present. No apologies were received.

2. MINUTES OF THE PREVIOUS MEETING
The minutes of the Q4 2025 meeting, having been circulated, were adopted as a true record and signed by the Chairman.

3. Q4 2025 FINANCIAL PERFORMANCE
The Managing Director presented the management accounts. Group revenue closed 12% above budget, driven by Liberty Pay processing volumes. KPMG confirmed no matters of emphasis arising from the interim review.

4. 2026 BUDGET APPROVAL
After discussion of the capital programme and headcount plan, IT WAS RESOLVED (CNI/BD/2026/001) that the 2026 group budget of N4.2bn be and is hereby approved.

5. DIVIDEND RECOMMENDATION
IT WAS RESOLVED (CNI/BD/2026/002) that a final dividend of 45 kobo per ordinary share be recommended to shareholders at the AGM, subject to audit completion.

6. ANY OTHER BUSINESS
The Board noted the CBN licence renewal timeline for Liberty Pay. There being no other business, the meeting closed at 12:14.

CONFIRMED AS A TRUE RECORD
Chief Adaeze Okonkwo — Chairman"""

        SAMPLE_BUDGET = """2026 GROUP BUDGET — BOARD PAPER
Prepared by: Group Finance | For approval at the Q1 2026 Board Meeting

1. SUMMARY
Management proposes a 2026 operating budget of N4.2bn (2025: N3.6bn), a 16.7% increase concentrated in payments infrastructure and agent-network expansion.

2. REVENUE ASSUMPTIONS
Liberty Pay: 28% volume growth on 12,000+ agents. Liberty Assured: premium income up 11%. CNI Properties: two disposals completing H2.

3. CAPITAL PROGRAMME
N920m capex: settlement platform re-architecture (N410m), northern-region agent rollout (N310m), office consolidation (N200m).

4. RISKS
FX exposure on imported hardware; CBN licence renewal timing; vendor concentration in switching. Sensitivities are set out in Appendix B.

5. RECOMMENDATION
The Board is invited to APPROVE the 2026 group budget of N4.2bn."""

        SAMPLE_RISK = """GROUP RISK REGISTER — Q2 2026 REVIEW
Prepared by: Group Risk & Compliance

TOP RISKS (RAG)
1. FX exposure on hardware imports — HIGH (was Medium). Naira depreciation of 9% QTD; mitigation: forward cover for H2 purchases.
2. Vendor concentration, switching services — HIGH (was Medium). Single provider handles 71% of volume; mitigation: second-provider onboarding by Q4.
3. CBN licence renewal (Liberty Pay) — MEDIUM. Submission pack in progress; deadline 15 August.
4. Data protection (NDPA) — MEDIUM. Subject-rights workflow live; annual audit scheduled Q3.
5. Agent fraud — MEDIUM. Chargeback rate 0.41%, within appetite; game-cashback controls tightened.

The Board is invited to NOTE the register and APPROVE the escalation of risks 1 and 2."""

        d_minutes = doc(holdco, "Minutes of the Q1 2026 Board Meeting (Signed)", q1, None, 6,
                        topic="Minutes", text=SAMPLE_MINUTES, downloadable=True)

        doc(holdco, "Q4 2025 Management Accounts", q1, "Q4 2025 financial performance", 34, topic="Finance",
            text="Q4 2025 MANAGEMENT ACCOUNTS\n\nGroup revenue N1.42bn (budget N1.27bn, +12%). EBITDA margin 31%. "
                 "Liberty Pay contributed 58% of group revenue on record Q4 volumes. Full schedules follow in Appendices A-F.")
        doc(holdco, "2026 Group Budget", q1, "2026 budget approval", 22, topic="Finance", text=SAMPLE_BUDGET, downloadable=True)
        doc(holdco, "Q1 2026 Management Accounts", q2, "Q1 2026 financial performance", 31, topic="Finance",
            text="Q1 2026 MANAGEMENT ACCOUNTS\n\nGroup revenue N1.08bn, 4% below budget on softer January volumes. "
                 "Management will present a recovery plan at the Q3 meeting. Cash position remains strong at N860m.")
        doc(holdco, "Group Risk Register — Q2 2026", q2, "Group risk register review", 18, topic="Risk", text=SAMPLE_RISK)
        doc(holdco, "H1 2026 Group Performance Report", q3, "H1 2026 group performance", 40, topic="Finance")
        d_land = doc(holdco, "CNI Properties — Lekki Land Acquisition Memo", q3, "CNI Properties land acquisition", 9, topic="Investment", late=True)
        doc(libertypay, "H1 Processing Volumes Report", lp_brd, "H1 processing volumes", 15, topic="Operations")
        doc(libertypay, "CBN Licence Renewal File", None, None, 27, topic="Regulatory")
        doc(holdco, "External Audit Plan 2026 (KPMG)", audit_cmte, "External audit plan", 12, committee="Audit")
        v2, created_v2 = DocumentVersion.objects.get_or_create(
            document=d_land, version_number=2,
            defaults=dict(content_hash=hashlib.sha256(b"lekki-v2").hexdigest(),
                          storage_key="demo/CNI/lekki-memo-v2.pdf",
                          text_content="Lekki land acquisition memo — revised pricing.", uploaded_by=cosec),
        )
        for m, v in ((q1, 1), (q2, 1), (q3, 1), (q3, 2)):
            BoardPack.objects.get_or_create(meeting=m, version_number=v, defaults=dict(published_by=cosec))

        # ---------- minutes ----------
        def minutes_for(m, state, blocks_text):
            mins, _ = Minutes.objects.get_or_create(meeting=m, defaults=dict(state=state))
            if mins.state != state:
                mins.state = state
                mins.save(update_fields=["state"])
            mins.attendees.set(board)
            for item_title, text in blocks_text.items():
                item = agenda_ix.get((m.pk, item_title))
                if item:
                    MinuteBlock.objects.get_or_create(minutes=mins, agenda_item=item, defaults=dict(text=text))
            # Seal signed minutes so the minute book verifies as intact (FR-MIN-3)
            if state == Minutes.State.SIGNED and not mins.content_hash:
                from apps.minutes.services import seal_signed
                seal_signed(minutes=mins, actor=cosec)
            return mins

        m1 = minutes_for(q1, Minutes.State.SIGNED, {
            "Minutes of previous meeting": "The minutes of the Q4 2025 meeting were adopted as a true record.",
            "Q4 2025 financial performance": "The Board reviewed Q4 performance. Revenue closed 12% above budget.",
            "2026 budget approval": "The 2026 group budget of N4.2bn was considered and approved.",
            "Dividend recommendation": "A final dividend of 45k per share was recommended for AGM approval.",
        })
        blk = MinuteBlock.objects.filter(minutes=m1, agenda_item=agenda_ix[(q1.pk, "2026 budget approval")]).first()
        if blk:
            InlineDecision.objects.get_or_create(block=blk, kind=InlineDecision.Kind.RESOLUTION,
                                                 text="THAT the 2026 group budget of N4.2bn be and is hereby approved.")
        m2 = minutes_for(q2, Minutes.State.CIRCULATED, {
            "Minutes of Q1 meeting": "The Q1 minutes were adopted without amendment.",
            "Q1 2026 financial performance": "Q1 revenue tracked 4% below budget; management to present recovery plan.",
            "Liberty Pay CBN licence renewal": "Cosec briefed the Board on the CBN licence renewal timeline.",
            "Group risk register review": "Two risks were escalated to High: FX exposure and vendor concentration.",
        })
        MinuteComment.objects.get_or_create(
            minutes=m2, author=dir1, text="Please reflect that I asked for a sensitivity analysis on FX exposure.",
        )
        MinuteComment.objects.get_or_create(
            minutes=m2, author=chairman, text="Item 4: add the agreed CBN submission deadline (15 August).",
            defaults=dict(dispositioned=True),
        )
        minutes_for(lp_brd, Minutes.State.ADOPTED, {
            "H1 processing volumes": "Volumes grew 31% HoH; agent count crossed 12,000.",
            "Agent-network expansion": "Approved expansion into 6 northern states.",
        })

        # ---------- resolutions ----------
        def resolution(e, num, title, text, m=None, kind=Resolution.Kind.BOARD,
                       outcome=Resolution.Outcome.PASSED, votes=None, threshold=0, expires=None):
            r, created = Resolution.objects.get_or_create(
                entity=e, number=num,
                defaults=dict(year=now.year, title=title, text=text, kind=kind, meeting=m,
                              mover=chairman, seconder=dir1, outcome=outcome,
                              effective_date=now.date(), threshold=threshold, expires_at=expires),
            )
            if created and votes:
                for voter, choice in votes:
                    Vote.objects.get_or_create(resolution=r, voter=voter, defaults=dict(choice=choice))
            return r

        r_budget = resolution(
            holdco, "CNI/BD/2026/001", "Approval of 2026 Group Budget",
            "THAT the 2026 group budget of N4.2bn be and is hereby approved.", m=q1,
            votes=[(u, Vote.Choice.FOR) for u in board],
        )
        resolution(
            holdco, "CNI/BD/2026/002", "Recommendation of Final Dividend",
            "THAT a final dividend of 45 kobo per ordinary share be recommended to shareholders.", m=q1,
            votes=[(u, Vote.Choice.FOR) for u in board[:5]] + [(dir4, Vote.Choice.ABSTAIN)],
        )
        resolution(
            holdco, "CNI/BD/2026/003", "Proposed Share Buy-back Programme",
            "THAT the company undertake a buy-back of up to 2% of issued shares.", m=q2,
            outcome=Resolution.Outcome.FAILED,
            votes=[(chairman, Vote.Choice.FOR), (md, Vote.Choice.FOR),
                   (dir1, Vote.Choice.AGAINST), (dir2, Vote.Choice.AGAINST), (dir3, Vote.Choice.AGAINST)],
        )
        r_circ = resolution(
            libertypay, "LP/BD/2026/004", "Circular: Opening of Settlement Account with Access Bank",
            "THAT the company open a settlement account with Access Bank Plc and that any two directors sign the mandate.",
            kind=Resolution.Kind.CIRCULAR, outcome=Resolution.Outcome.PENDING,
            threshold=4, expires=now + timedelta(days=10),
        )
        for signer in (chairman, md, dir3):
            Signature.objects.get_or_create(resolution=r_circ, signer=signer,
                                            defaults=dict(certificate=f"demo-cert-{signer.email}"))
        # further circulars in flight — these sit in the cosec's signature queue
        r_circ2 = resolution(
            holdco, "CNI/BD/2026/005", "Circular: Appointment of Additional Bankers",
            "THAT the company open operating accounts with Zenith Bank Plc and that the Company Secretary "
            "be authorised to complete the account-opening formalities.",
            kind=Resolution.Kind.CIRCULAR, outcome=Resolution.Outcome.PENDING,
            threshold=4, expires=now + timedelta(days=14),
        )
        for signer in (chairman, dir1):
            Signature.objects.get_or_create(resolution=r_circ2, signer=signer,
                                            defaults=dict(certificate=f"demo-cert-{signer.email}"))
        r_circ3 = resolution(
            assured, "LA/BD/2026/006", "Circular: Renewal of Reinsurance Treaty",
            "THAT the 2026/27 reinsurance treaty be renewed on the terms presented, and that the Managing "
            "Director be authorised to execute the treaty documents.",
            kind=Resolution.Kind.CIRCULAR, outcome=Resolution.Outcome.PENDING,
            threshold=3, expires=now + timedelta(days=6),
        )
        Signature.objects.get_or_create(resolution=r_circ3, signer=md,
                                        defaults=dict(certificate=f"demo-cert-{md.email}"))
        CertifiedTrueCopy.objects.get_or_create(
            resolution=r_budget, reference="CTC/CNI/2026/001",
            defaults=dict(issued_by=cosec,
                          body="Certified a true copy of the resolution passed at the Q1 2026 Board Meeting."),
        )

        # ---------- actions ----------
        def act(e, title, owner, due_days, m=None, status=Action.Status.OPEN, evidence=""):
            Action.objects.get_or_create(
                entity=e, title=title,
                defaults=dict(owner=owner, meeting=m, due_date=now.date() + timedelta(days=due_days),
                              status=status, evidence=evidence),
            )

        act(holdco, "Circulate approved 2026 budget to subsidiary MDs", cosec, -60, q1,
            Action.Status.DONE, "Emailed 12 Jan; acknowledgements on file.")
        act(holdco, "Present FX sensitivity analysis to the Board", md, -5, q2)  # overdue
        act(holdco, "File CBN licence renewal for Liberty Pay", cosec, 12, q2)
        act(holdco, "Engage valuer for Lekki land parcel", dir1, 18, q3)
        act(libertypay, "Complete agent onboarding audit for northern expansion", dir3, 25, lp_brd)
        act(holdco, "Close out two High risks on the risk register", md, 30, q2)
        # more overdue items (chasing depth on the dashboard)
        act(holdco, "Circulate draft Q2 minutes to the Board for comment", cosec, -9, q2)   # overdue + mine
        act(assured, "Submit NAICOM quarterly returns evidence", dir4, -3, None)            # overdue
        # more items owned by the Company Secretary
        act(holdco, "Prepare AGM notice and proxy forms", cosec, 15, agm)
        act(holdco, "Update the register of directors' interests after Q2 declarations", cosec, 22, q2)
        act(libertypay, "Assemble CBN licence renewal submission pack", cosec, 8, lp_q3)

        # ---------- registers ----------
        def reg(e, rtype, party, frm_days, particulars=None, ceased_days=None):
            # update_or_create so reseeding enriches existing entries' particulars
            RegisterEntry.objects.update_or_create(
                entity=e, register_type=rtype, party_name=party,
                defaults=dict(effective_from=now.date() - timedelta(days=frm_days),
                              ceased_on=(now.date() - timedelta(days=ceased_days)) if ceased_days else None,
                              particulars=particulars or {}),
            )

        # KYC particulars per director (demo data — BVNs/documents are fictitious)
        def kyc(designation, bvn, doc_type, doc_no, dob, occupation, email, phone, address, others=None, expiry="2030-06-30"):
            return {
                "designation": designation, "full_name": None, "bvn": bvn,
                "document_type": doc_type, "document_number": doc_no, "document_expiry": expiry,
                "date_of_birth": dob, "nationality": "Nigerian", "occupation": occupation,
                "email": email, "phone": phone, "residential_address": address,
                "other_directorships": others or [],
            }

        KYC = {
            "Chief Adaeze Okonkwo": kyc("Chairman", "22110000101", "International Passport", "A08123456",
                "1962-04-18", "Company Director", "chairman@cnigroup.demo", "+234 803 100 0001",
                "4 Bourdillon Road, Ikoyi, Lagos", ["Sable Capital Partners", "Okonkwo Family Trust"]),
            "Emeka Nwachukwu": kyc("Managing Director", "22110000102", "Driver's Licence", "LAG-45812-XY",
                "1975-11-02", "Banker", "md@cnigroup.demo", "+234 803 100 0002",
                "12b Glover Road, Ikoyi, Lagos", ["Liberty Pay Limited"]),
            "Folake Balogun": kyc("Non-Executive Director", "22110000103", "International Passport", "A07654321",
                "1968-07-25", "Chartered Accountant", "f.balogun@cnigroup.demo", "+234 803 100 0003",
                "3 Queens Drive, Ikoyi, Lagos", ["Balogun & Co (Managing Partner)"]),
            "Talatu Danjuma": kyc("Independent Director", "22110000104", "National ID (NIN)", "NIN-63125478901",
                "1971-01-30", "Economist", "t.danjuma@cnigroup.demo", "+234 803 100 0004",
                "22 Mississippi Street, Maitama, Abuja"),
            "Kelechi Eze": kyc("Non-Executive Director", "22110000105", "International Passport", "A09811223",
                "1979-09-14", "Engineer", "k.eze@cnigroup.demo", "+234 803 100 0005",
                "7 Chevron Drive, Lekki, Lagos", ["Eze Industrial Holdings"]),
            "Amina Suleiman": kyc("Non-Executive Director", "22110000106", "Driver's Licence", "KAN-77120-AB",
                "1980-03-08", "Lawyer", "a.suleiman@cnigroup.demo", "+234 803 100 0006",
                "15 Race Course Road, Nassarawa GRA, Kano"),
            "Bolanle Craig (resigned)": kyc("NED", "22110000107", "International Passport", "A05500991",
                "1958-12-01", "Retired Banker", "b.craig@cnigroup.demo", "+234 803 100 0007",
                "9 Milverton Road, Ikoyi, Lagos"),
        }

        for e in (holdco, libertypay, assured, props):
            reg(e, RegisterType.MEMBERS, "C&I Leasing Plc" if e is not holdco else "Okonkwo Family Trust",
                3000, {"shares": 60_000_000, "class": "ordinary"})
            reg(e, RegisterType.MEMBERS, "Sable Capital Partners", 2200, {"shares": 25_000_000, "class": "ordinary"})
            reg(e, RegisterType.DIRECTORS, "Chief Adaeze Okonkwo", 2800, KYC["Chief Adaeze Okonkwo"])
            reg(e, RegisterType.DIRECTORS, "Emeka Nwachukwu", 2400, KYC["Emeka Nwachukwu"])
            reg(e, RegisterType.SECRETARIES, "Inyang Inyangete", 1500, {"appointment": "Group Company Secretary"})
        reg(holdco, RegisterType.DIRECTORS, "Bolanle Craig (resigned)", 3200, KYC["Bolanle Craig (resigned)"], ceased_days=400)
        reg(holdco, RegisterType.BENEFICIAL_OWNERS, "Chief Adaeze Okonkwo", 3000, {"control": "32% indirect"})
        # directors' personal shareholdings (joined into the Directors view)
        reg(holdco, RegisterType.MEMBERS, "Chief Adaeze Okonkwo", 2800, {"shares": 8_000_000, "class": "ordinary"})
        reg(holdco, RegisterType.MEMBERS, "Emeka Nwachukwu", 2400, {"shares": 4_500_000, "class": "ordinary"})
        reg(holdco, RegisterType.MEMBERS, "Folake Balogun", 2000, {"shares": 1_200_000, "class": "ordinary"})
        reg(holdco, RegisterType.MEMBERS, "Talatu Danjuma", 1800, {"shares": 750_000, "class": "ordinary"})
        # more directors on the register so the roster is full
        reg(holdco, RegisterType.DIRECTORS, "Folake Balogun", 2000, KYC["Folake Balogun"])
        reg(holdco, RegisterType.DIRECTORS, "Talatu Danjuma", 1800, KYC["Talatu Danjuma"])
        reg(holdco, RegisterType.DIRECTORS, "Kelechi Eze", 1600, KYC["Kelechi Eze"])
        reg(holdco, RegisterType.DIRECTORS, "Amina Suleiman", 1500, KYC["Amina Suleiman"])
        reg(libertypay, RegisterType.DIRECTORS, "Kelechi Eze", 1400, KYC["Kelechi Eze"])
        reg(assured, RegisterType.DIRECTORS, "Amina Suleiman", 1300, KYC["Amina Suleiman"])
        reg(libertypay, RegisterType.CHARGES, "Access Bank Plc — debenture over receivables", 700,
            {"amount": 500_000_000, "currency": "NGN"})

        # ---------- committees ----------
        from apps.committees.models import Committee, CommitteeMembership, CommitteeReport

        def committee(e, name, charter, chair, members, chair_term_end=None):
            com, _ = Committee.objects.get_or_create(
                entity=e, name=name,
                defaults=dict(charter=charter, charter_adopted_on=now.date() - timedelta(days=500)),
            )
            CommitteeMembership.objects.get_or_create(
                committee=com, user=chair, role=CommitteeMembership.Role.CHAIR,
                defaults=dict(term_start=now.date() - timedelta(days=400), term_end=chair_term_end),
            )
            for m in members:
                CommitteeMembership.objects.get_or_create(
                    committee=com, user=m, role=CommitteeMembership.Role.MEMBER,
                    defaults=dict(term_start=now.date() - timedelta(days=400),
                                  term_end=now.date() + timedelta(days=365)),
                )
            return com

        audit_com = committee(
            holdco, "Audit Committee",
            "TERMS OF REFERENCE\n\n1. Oversee the integrity of financial statements and the external audit.\n"
            "2. Review internal controls and the internal audit programme.\n"
            "3. Recommend the appointment and remuneration of the external auditor.\n"
            "4. Report to the Board after each committee meeting.",
            dir1, [dir3, dir4],
            chair_term_end=now.date() + timedelta(days=45),  # expiring soon -> rotation flag
        )
        risk_com = committee(
            holdco, "Board Risk Committee",
            "TERMS OF REFERENCE\n\n1. Own the group risk appetite and register.\n"
            "2. Review top risks quarterly and escalation thresholds.\n"
            "3. Oversee regulatory compliance (CBN, NDPA) across subsidiaries.",
            dir2, [dir4, md],
        )
        CommitteeReport.objects.get_or_create(
            committee=audit_com, title="Q2 2026 Audit Committee Report",
            defaults=dict(
                summary="The Committee reviewed the external audit plan and interim findings. "
                        "No material weaknesses identified; two process improvements agreed with management.",
                submitted_by=dir1, meeting=q3, status=CommitteeReport.Status.SUBMITTED,
            ),
        )
        CommitteeReport.objects.get_or_create(
            committee=risk_com, title="Q2 2026 Risk Committee Report",
            defaults=dict(
                summary="FX exposure and vendor concentration escalated to High; mitigation plans tracked. "
                        "Risk appetite statement due for annual refresh in Q4.",
                submitted_by=dir2, meeting=q3, status=CommitteeReport.Status.NOTED,
            ),
        )

        # ---------- delegation of authority ----------
        from apps.resolutions.models import DelegationRule

        def doa(e, category, tiers):
            for tier, (approver, limit) in enumerate(tiers, start=1):
                DelegationRule.objects.get_or_create(
                    entity=e, category=category, tier=tier,
                    defaults=dict(approver=approver, max_amount=limit),
                )

        doa(holdco, "Capital expenditure", [
            ("Managing Director", 50_000_000), ("Board Finance Committee", 250_000_000), ("Full Board", 1_000_000_000)])
        doa(holdco, "Asset disposals", [
            ("Managing Director", 25_000_000), ("Full Board", 500_000_000)])
        doa(holdco, "Contracts & procurement", [
            ("Managing Director", 100_000_000), ("Full Board", 750_000_000)])
        doa(libertypay, "Capital expenditure", [
            ("CEO", 30_000_000), ("Board", 300_000_000)])

        # ---------- compliance calendar ----------
        from apps.compliance.models import ComplianceObligation, Filing

        def obligation(e, title, regulator, freq, due_in_days, description="", filed=None):
            ob, _ = ComplianceObligation.objects.update_or_create(
                entity=e, title=title,
                defaults=dict(regulator=regulator, frequency=freq,
                              due_date=now.date() + timedelta(days=due_in_days),
                              description=description),
            )
            if filed:
                Filing.objects.get_or_create(
                    obligation=ob, period_label=filed[0],
                    defaults=dict(filed_on=now.date() - timedelta(days=filed[1]),
                                  evidence=filed[2], filed_by=cosec),
                )
            return ob

        obligation(holdco, "CAC Annual Return", "CAC", "annual", 18,
                   "Annual return under CAMA s.417 for the holding company.",
                   filed=("FY2024", 380, "CAC/AR/2024/55102"))
        obligation(libertypay, "CBN PSP Licence Renewal", "CBN", "annual", -12,
                   "Payment service provider licence renewal — submission pack required.")
        obligation(holdco, "FIRS Companies Income Tax Filing", "FIRS", "annual", 150,
                   "CIT self-assessment filing for the group.",
                   filed=("FY2024", 200, "FIRS e-ack 2024-CIT-88231"))
        obligation(holdco, "NDPC Data Protection Audit", "NDPC", "annual", 55,
                   "Annual data protection compliance audit filing under NDPA.")
        obligation(assured, "NAICOM Annual Returns", "NAICOM", "annual", 40,
                   "Insurance regulatory annual returns.")

        # ---------- announcements ----------
        from apps.announcements.models import Announcement, ReadReceipt

        ann, _ = Announcement.objects.get_or_create(
            entity=holdco, title="Q3 Board Circular — pre-reading",
            defaults=dict(
                body="Directors are asked to review the Q3 board pack ahead of the meeting, "
                     "with particular attention to the FX sensitivity analysis and the CBN "
                     "licence-renewal timeline. Please raise any questions with the Company "
                     "Secretary by end of week.",
                posted_by=chairman),
        )
        for u in (dir1, dir2):  # a couple have read it; others haven't (visible receipts)
            ReadReceipt.objects.get_or_create(announcement=ann, user=u)

        # ---------- notifications ----------
        def note(recipient, event_type, subject, body, link="", read=False):
            Notification.objects.get_or_create(
                recipient=recipient, event_type=event_type, subject=subject, channel="in_portal",
                defaults=dict(body=body, link=link, read=read),
            )

        note(cosec, "pack.published", "Q3 2026 board pack v2 published",
             "The revised Q3 pack (incl. late Lekki memo) is available.", "/meetings", False)
        note(cosec, "resolution.circulated", "Circular resolution awaiting signatures",
             "LP/BD/2026/004 needs 1 more signature to pass.", "/resolutions", False)
        note(cosec, "minutes.circulated", "Q2 minutes circulated for comment",
             "Two comments received; one still open.", "/minutes", True)
        note(cosec, "action.overdue", "Action overdue: FX sensitivity analysis",
             "Due 5 days ago — owner: Emeka Nwachukwu.", "/actions", False)
        for u in board:
            note(u, "meeting.scheduled", "Q3 2026 Board Meeting scheduled",
                 "Convening on the 21st; joining link in the meeting workspace.", "/meetings")

        # ---------- audit colour ----------
        def audit(action, actor, target, **meta):
            if not AuditEvent.objects.filter(action=action, actor=actor).exists():
                AuditEvent.objects.record(action=action, actor=actor, target=target, metadata=meta or {})

        audit("meeting.created", cosec, q3)
        audit("pack.published", cosec, q3, version=2)
        audit("document.viewed", chairman, d_land)
        audit("document.viewed", dir1, d_land)
        audit("resolution.signed", md, r_circ)
        audit("minutes.circulated", cosec, m2)
        audit("register.entry.added", cosec, holdco)

        # ---------- summary ----------
        out(self.style.SUCCESS("Seed complete."))
        for label, qs in [
            ("users", User.objects), ("entities", Entity.objects), ("meetings", Meeting.objects),
            ("agenda items", AgendaItem.objects), ("attendance", Attendance.objects),
            ("documents", Document.objects), ("versions", DocumentVersion.objects),
            ("board packs", BoardPack.objects), ("minutes", Minutes.objects),
            ("minute blocks", MinuteBlock.objects), ("comments", MinuteComment.objects),
            ("resolutions", Resolution.objects), ("votes", Vote.objects),
            ("signatures", Signature.objects), ("CTCs", CertifiedTrueCopy.objects),
            ("actions", Action.objects), ("register entries", RegisterEntry.objects),
            ("notifications", Notification.objects), ("audit events", AuditEvent.objects),
        ]:
            out(f"  {label:18} {qs.count()}")
        out(self.style.WARNING(f"Demo director accounts use password: {DEMO_PASSWORD}"))
        out(f"{COSEC_EMAIL} untouched if it already existed (now group cosec + admin).")
