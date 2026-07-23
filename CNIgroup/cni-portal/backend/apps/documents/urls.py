from rest_framework.routers import DefaultRouter

from .api import AnnotationViewSet, DocumentViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("annotations", AnnotationViewSet, basename="annotation")

urlpatterns = router.urls
