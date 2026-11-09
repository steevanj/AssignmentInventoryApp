from django.contrib import admin
from django.urls import include, path, re_path

from core.api import ApiNotFoundView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/products/", include("products.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/reports/", include("reports.urls")),
    re_path(r"^api/", ApiNotFoundView.as_view()),
]
