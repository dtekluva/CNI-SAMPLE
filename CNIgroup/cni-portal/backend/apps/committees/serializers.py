from rest_framework import serializers

from .models import Committee, CommitteeMembership, CommitteeReport


class MembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    expires_soon = serializers.BooleanField(read_only=True)

    class Meta:
        model = CommitteeMembership
        fields = ["id", "committee", "user", "user_name", "role", "term_start", "term_end",
                  "ended_on", "is_active", "expires_soon"]
        read_only_fields = ["id", "ended_on", "is_active", "expires_soon"]

    def get_user_name(self, obj):
        return obj.user.name or obj.user.email


class ReportSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.SerializerMethodField()
    committee_name = serializers.CharField(source="committee.name", read_only=True)

    class Meta:
        model = CommitteeReport
        fields = ["id", "committee", "committee_name", "meeting", "title", "summary",
                  "status", "submitted_by", "submitted_by_name", "submitted_at", "noted_at"]
        read_only_fields = ["id", "status", "submitted_by", "submitted_at", "noted_at"]

    def get_submitted_by_name(self, obj):
        if not obj.submitted_by_id:
            return None
        return obj.submitted_by.name or obj.submitted_by.email


class CommitteeSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source="entity.legal_name", read_only=True)
    memberships = MembershipSerializer(many=True, read_only=True)
    reports_count = serializers.IntegerField(source="reports.count", read_only=True)

    class Meta:
        model = Committee
        fields = ["id", "entity", "entity_name", "name", "charter", "charter_adopted_on",
                  "memberships", "reports_count", "created_at"]
        read_only_fields = ["id", "created_at"]
