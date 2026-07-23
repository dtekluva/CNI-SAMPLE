from rest_framework import serializers

from .models import Entity


class EntitySerializer(serializers.ModelSerializer):
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = Entity
        fields = [
            "id",
            "parent",
            "legal_name",
            "cac_rc_number",
            "incorporation_date",
            "registered_address",
            "share_capital",
            "financial_year_end",
            "company_secretary",
            "auditors",
            "regulators",
            "is_complete",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_complete", "created_at", "updated_at"]
