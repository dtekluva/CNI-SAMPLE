from rest_framework import serializers

from .models import ConflictDeclaration, InterestDeclaration


class InterestSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    director_name = serializers.CharField(source="director.name", read_only=True)

    class Meta:
        model = InterestDeclaration
        fields = [
            "id", "entity", "director", "director_name", "kind", "kind_display",
            "party", "details", "declared_on", "withdrawn_on", "is_active", "created_at",
        ]
        read_only_fields = ["id", "director", "withdrawn_on", "is_active", "created_at"]


class ConflictSerializer(serializers.ModelSerializer):
    director_name = serializers.CharField(source="director.name", read_only=True)

    class Meta:
        model = ConflictDeclaration
        fields = ["id", "meeting", "agenda_item", "director", "director_name", "interest", "note", "declared_at"]
        read_only_fields = ["id", "director", "declared_at"]
        # unique_together includes nullable agenda_item; DRF's auto validator would
        # force it to be required, breaking whole-meeting declarations. The service
        # get_or_create handles idempotency instead.
        validators = []
