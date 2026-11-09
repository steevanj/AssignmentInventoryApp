from django.contrib import admin

from .models import SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    readonly_fields = ["product", "quantity", "rate", "amount"]
    can_delete = False


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    """Read-only view; orders are created and changed through the app so totals stay correct."""

    list_display = ["order_number", "customer", "order_date", "status", "grand_total", "created_by"]
    list_filter = ["status", "order_date"]
    search_fields = ["order_number", "customer__name"]
    inlines = [SalesOrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
