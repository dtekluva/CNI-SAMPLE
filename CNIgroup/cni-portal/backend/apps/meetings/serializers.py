from rest_framework import serializers

from .models import AgendaItem, Meeting


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            "id", "entity", "title", "meeting_type", "starts_at", "timezone",
            "location", "is_virtual", "virtual_link", "virtual_provider", "dial_in",
            "recording_url", "quorum", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AgendaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaItem
        fields = ["id", "title", "item_type", "owner", "time_allocation_minutes", "position"]
        read_only_fields = ["id", "position"]
