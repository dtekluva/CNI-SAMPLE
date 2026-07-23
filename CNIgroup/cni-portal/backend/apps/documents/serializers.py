from rest_framework import serializers

from .models import Annotation, Document, OfflinePackGrant


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "entity", "title", "access_mode", "committee", "topic",
            "meeting", "agenda_item", "page_count", "is_late",
            "retention_until", "legal_hold", "purged", "purged_at", "created_at",
        ]
        read_only_fields = ["id", "purged", "purged_at", "created_at"]


class AnnotationSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Annotation
        fields = ["id", "document", "author", "author_name", "page", "text",
                  "visibility", "shared_with", "created_at"]
        read_only_fields = ["id", "document", "author", "created_at"]

    def get_author_name(self, obj):
        return obj.author.name or obj.author.email


class OfflineGrantSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = OfflinePackGrant
        fields = ["id", "meeting", "user", "user_name", "device", "status",
                  "granted_at", "revoked_at", "synced_at"]
        read_only_fields = ["id", "user", "status", "granted_at", "revoked_at", "synced_at"]

    def get_user_name(self, obj):
        return obj.user.name or obj.user.email
