from django.urls import path

from .views import StockAdjustmentView

app_name = "inventory"

urlpatterns = [
    path("adjustments/", StockAdjustmentView.as_view(), name="adjust"),
]
