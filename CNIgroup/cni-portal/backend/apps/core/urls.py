from django.urls import path

from .views import dashboard, export_view, global_search_view, health

urlpatterns = [
    path("health/", health, name="health"),
    path("dashboard/", dashboard, name="dashboard"),
    path("search/", global_search_view, name="global-search"),
    path("exports/<str:kind>/", export_view, name="export"),
]
