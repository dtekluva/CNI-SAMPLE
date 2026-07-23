from django.contrib import admin

from .models import ComplianceObligation, Filing


@admin.register(ComplianceObligation)
class ObligationAdmin(admin.ModelAdmin):
    list_display = ("title", "entity", "regulator", "frequency", "due_date")
    list_filter = ("regulator", "entity")


@admin.register(Filing)
class FilingAdmin(admin.ModelAdmin):
    list_display = ("obligation", "period_label", "filed_on", "filed_by")
