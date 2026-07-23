from rest_framework import serializers

from .models import Action


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = [
            "id", "entity", "meeting", "agenda_item", "title", "owner",
            "owner_name", "due_date", "status", "evidence", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
