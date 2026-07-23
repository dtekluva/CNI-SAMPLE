from rest_framework.routers import DefaultRouter

from .api import ConflictViewSet, InterestViewSet

router = DefaultRouter()
router.register("interests", InterestViewSet, basename="interest")
router.register("conflicts", ConflictViewSet, basename="conflict")

urlpatterns = router.urls
