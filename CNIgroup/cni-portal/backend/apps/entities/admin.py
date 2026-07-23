from django.contrib import admin

from .models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "cac_rc_number", "parent", "is_complete")
    search_fields = ("legal_name", "cac_rc_number")
    list_filter = ("parent",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Complete")
    def is_complete(self, obj):
        return obj.is_complete
