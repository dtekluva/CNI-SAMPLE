from django.contrib import admin

from .models import Document, DocumentVersion


class VersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ("version_number", "content_hash", "uploaded_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "entity", "committee", "topic", "created_at")
    list_filter = ("entity", "committee")
    search_fields = ("title", "topic")
    inlines = [VersionInline]
