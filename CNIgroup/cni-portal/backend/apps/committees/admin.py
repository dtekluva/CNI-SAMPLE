from django.contrib import admin

from .models import Committee, CommitteeMembership, CommitteeReport


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = ("name", "entity", "charter_adopted_on")
    list_filter = ("entity",)


@admin.register(CommitteeMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("committee", "user", "role", "term_start", "term_end", "ended_on")


@admin.register(CommitteeReport)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "committee", "status", "submitted_at")
