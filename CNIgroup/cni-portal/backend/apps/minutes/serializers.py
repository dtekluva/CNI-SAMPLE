from rest_framework import serializers

from .models import MinuteBlock, Minutes


class MinuteBlockSerializer(serializers.ModelSerializer):
    agenda_item_title = serializers.CharField(source="agenda_item.title", read_only=True)
    agenda_item_position = serializers.IntegerField(source="agenda_item.position", read_only=True)

    class Meta:
        model = MinuteBlock
        fields = ["id", "agenda_item", "agenda_item_title", "agenda_item_position", "text"]


class MinutesSerializer(serializers.ModelSerializer):
    blocks = MinuteBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Minutes
        fields = ["id", "state", "attendees", "blocks"]
        read_only_fields = ["id", "state", "attendees", "blocks"]
