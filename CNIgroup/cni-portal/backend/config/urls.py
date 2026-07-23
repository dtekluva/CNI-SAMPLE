from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.entities.urls")),
    path("api/", include("apps.registers.urls")),
    path("api/", include("apps.conflicts.urls")),
    path("api/", include("apps.rbac.urls")),
    path("api/", include("apps.minutes.urls")),
    path("api/", include("apps.committees.urls")),
    path("api/", include("apps.compliance.urls")),
    path("api/", include("apps.announcements.urls")),
    path("api/", include("apps.meetings.urls")),
    path("api/", include("apps.documents.urls")),
    path("api/", include("apps.resolutions.urls")),
    path("api/", include("apps.actions.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.audit.urls")),
]
