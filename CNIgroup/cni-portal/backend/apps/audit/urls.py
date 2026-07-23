from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import AuditEventViewSet, integrity

router = DefaultRouter()
router.register("audit", AuditEventViewSet, basename="audit")

urlpatterns = [path("integrity/", integrity)] + router.urls
