from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "name")
    ordering = ("email",)
    list_filter = ("is_staff", "is_active")
    readonly_fields = ("last_login", "date_joined")
