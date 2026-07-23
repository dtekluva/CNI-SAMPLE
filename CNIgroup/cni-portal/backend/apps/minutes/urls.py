from rest_framework.routers import DefaultRouter

from .api import MinuteBookViewSet

router = DefaultRouter()
router.register("minute-book", MinuteBookViewSet, basename="minutebook")

urlpatterns = router.urls
