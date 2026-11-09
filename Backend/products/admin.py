from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["product_code", "name", "category", "price", "stock_quantity", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["product_code", "name"]
    # stock must only change through adjustments/orders so a movement is always recorded
    readonly_fields = ["stock_quantity"]
