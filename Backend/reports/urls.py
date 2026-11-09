from django.urls import path

from .views import CustomerSalesReportView, LowStockReportView, ProductSalesReportView, StockMovementReportView

app_name = "reports"

urlpatterns = [
    path("customer-sales/", CustomerSalesReportView.as_view(), name="customer-sales"),
    path("product-sales/", ProductSalesReportView.as_view(), name="product-sales"),
    path("low-stock/", LowStockReportView.as_view(), name="low-stock"),
    path("stock-movements/", StockMovementReportView.as_view(), name="stock-movements"),
]
