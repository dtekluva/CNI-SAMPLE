from rest_framework.routers import DefaultRouter

from .api import RegisterEntryViewSet

router = DefaultRouter()
router.register("registers", RegisterEntryViewSet, basename="register")

urlpatterns = router.urls
