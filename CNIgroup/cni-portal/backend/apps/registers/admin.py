from django.contrib import admin

from .models import RegisterEntry


@admin.register(RegisterEntry)
class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = ("entity", "register_type", "party_name", "effective_from", "ceased_on")
    list_filter = ("register_type", "entity", "ceased_on")
    search_fields = ("party_name",)
