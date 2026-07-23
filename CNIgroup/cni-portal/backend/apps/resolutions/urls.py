from rest_framework.routers import DefaultRouter

from .api import DelegationRuleViewSet, ResolutionViewSet

router = DefaultRouter()
router.register("resolutions", ResolutionViewSet, basename="resolution")
router.register("doa", DelegationRuleViewSet, basename="doa")

urlpatterns = router.urls
