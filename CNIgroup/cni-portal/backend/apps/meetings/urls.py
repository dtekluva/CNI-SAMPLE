from rest_framework.routers import DefaultRouter

from .api import MeetingViewSet

router = DefaultRouter()
router.register("meetings", MeetingViewSet, basename="meeting")

urlpatterns = router.urls
