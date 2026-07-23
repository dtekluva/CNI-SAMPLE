from rest_framework.routers import DefaultRouter

from .api import ActionViewSet

router = DefaultRouter()
router.register("actions", ActionViewSet, basename="action")

urlpatterns = router.urls
