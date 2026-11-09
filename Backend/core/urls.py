from django.contrib import admin
from django.urls import include, path, re_path

from core.api import ApiNotFoundView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    re_path(r"^api/", ApiNotFoundView.as_view()),
]
