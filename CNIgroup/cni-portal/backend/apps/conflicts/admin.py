from django.contrib import admin

from .models import ConflictDeclaration, InterestDeclaration


@admin.register(InterestDeclaration)
class InterestAdmin(admin.ModelAdmin):
    list_display = ("director", "entity", "kind", "party", "declared_on", "withdrawn_on")
    list_filter = ("kind", "entity")


@admin.register(ConflictDeclaration)
class ConflictAdmin(admin.ModelAdmin):
    list_display = ("director", "meeting", "agenda_item", "declared_at")
