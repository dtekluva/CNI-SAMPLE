from django.contrib import admin

from .models import RoleAssignment


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "entity", "is_group_level", "created_at")
    list_filter = ("role", "entity")
    search_fields = ("user__email",)
    readonly_fields = ("created_at",)
