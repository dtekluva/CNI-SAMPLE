from django.contrib import admin

from .models import Meeting


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "entity", "meeting_type", "starts_at", "is_virtual")
    list_filter = ("meeting_type", "entity", "is_virtual")
    search_fields = ("title",)
    date_hierarchy = "starts_at"
