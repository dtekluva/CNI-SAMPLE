from rest_framework.routers import DefaultRouter

from .api import ObligationViewSet

router = DefaultRouter()
router.register("compliance", ObligationViewSet, basename="compliance")

urlpatterns = router.urls
