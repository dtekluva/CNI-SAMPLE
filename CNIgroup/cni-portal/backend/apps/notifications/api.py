from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer
from .services import set_preference


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """My notifications (FR-NOT-1) + channel preferences. Personal (recipient-scoped)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsMFAVerified]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = self.get_object()
        n.read = True
        n.save(update_fields=["read"])
        return Response({"read": True})

    @action(detail=False, methods=["get", "post"])
    def preferences(self, request):
        if request.method == "POST":
            set_preference(
                user=request.user,
                event_type=request.data["event_type"],
                channel=request.data["channel"],
                enabled=request.data["enabled"],
            )
            return Response({"ok": True}, status=201)
        prefs = NotificationPreference.objects.filter(user=request.user).values(
            "event_type", "channel", "enabled"
        )
        return Response(list(prefs))
