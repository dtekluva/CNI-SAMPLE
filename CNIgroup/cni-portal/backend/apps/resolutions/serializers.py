from rest_framework import serializers

from .models import DelegationRule, Resolution


class DelegationRuleSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source="entity.legal_name", read_only=True)

    class Meta:
        model = DelegationRule
        fields = ["id", "entity", "entity_name", "category", "approver", "max_amount", "tier", "created_at"]
        read_only_fields = ["id", "created_at"]


class ResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resolution
        fields = [
            "id", "entity", "meeting", "number", "year", "title", "text", "kind",
            "voting_mode", "resolution_class", "amount", "category",
            "mover", "seconder", "outcome", "effective_date", "threshold",
            "expires_at", "created_at",
        ]
        read_only_fields = ["id", "number", "year", "outcome", "effective_date", "created_at"]
