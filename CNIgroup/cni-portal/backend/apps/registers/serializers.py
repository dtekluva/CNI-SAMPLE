from rest_framework import serializers

from .models import RegisterEntry


class RegisterEntrySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    register_type_display = serializers.CharField(source="get_register_type_display", read_only=True)

    class Meta:
        model = RegisterEntry
        fields = [
            "id",
            "entity",
            "register_type",
            "register_type_display",
            "party_name",
            "particulars",
            "effective_from",
            "ceased_on",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_active", "register_type_display", "ceased_on", "created_at", "updated_at"]
