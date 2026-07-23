from rest_framework.routers import DefaultRouter

from .api import CommitteeViewSet

router = DefaultRouter()
router.register("committees", CommitteeViewSet, basename="committee")

urlpatterns = router.urls
