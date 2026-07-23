from rest_framework.routers import DefaultRouter

from .api import RoleAssignmentViewSet

router = DefaultRouter()
router.register("roles", RoleAssignmentViewSet, basename="role")

urlpatterns = router.urls
