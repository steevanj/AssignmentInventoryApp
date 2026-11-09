from django.urls import path

from .views import OrderCancelView, OrderConfirmView, OrderDetailView, OrderListCreateView

app_name = "orders"

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="list"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/confirm/", OrderConfirmView.as_view(), name="confirm"),
    path("<int:pk>/cancel/", OrderCancelView.as_view(), name="cancel"),
]
