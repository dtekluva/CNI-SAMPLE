from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id", "actor", "action", "content_type", "object_id", "metadata",
            "ip_address", "device", "timestamp", "hash",
        ]
        read_only_fields = fields
