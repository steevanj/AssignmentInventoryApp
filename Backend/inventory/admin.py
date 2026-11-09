from django.contrib import admin

from .models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """The stock ledger is append-only, so the admin only lets you look at it."""

    list_display = ["created_at", "product", "movement_type", "quantity_change", "stock_after",
                    "related_order", "created_by"]
    list_filter = ["movement_type"]
    search_fields = ["product__product_code", "product__name", "reason"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
