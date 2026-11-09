"""
Every change to Product.stock_quantity goes through this module, so each
change is checked (stock never goes negative) and always leaves a
StockMovement record behind.

Callers must already be inside transaction.atomic() and hold a row lock
on the product (see lock_products) - that is what makes two users
confirming orders at the same time safe.
"""

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from inventory.models import StockMovement
from products.models import Product


def lock_products(product_ids):
    """
    SELECT ... FOR UPDATE on the given products and return {id: product}.

    Rows are locked in id order. If every transaction locks in the same
    order, two transactions can never each hold a lock the other needs,
    so they cannot deadlock.
    """
    products = Product.objects.select_for_update().filter(pk__in=set(product_ids)).order_by("pk")
    return {product.pk: product for product in products}


def change_stock(product, quantity_change, movement_type, user, reason, order=None):
    """Apply a signed change to a locked product row and record the movement."""
    new_stock = product.stock_quantity + quantity_change
    if new_stock < 0:
        raise ValidationError(
            f"Not enough stock for {product.product_code} ({product.name}): "
            f"{product.stock_quantity} available, {abs(quantity_change)} requested."
        )

    product.stock_quantity = new_stock
    product.save(update_fields=["stock_quantity", "updated_at"])

    return StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity_change=quantity_change,
        stock_after=new_stock,
        related_order=order,
        reason=reason,
        created_by=user,
    )


def record_opening_stock(product, user, reason="Opening stock"):
    """Log the starting stock of a newly created product (no-op when it is 0)."""
    if product.stock_quantity <= 0:
        return None
    return StockMovement.objects.create(
        product=product,
        movement_type=StockMovement.MovementType.OPENING,
        quantity_change=product.stock_quantity,
        stock_after=product.stock_quantity,
        reason=reason,
        created_by=user,
    )


def adjust_stock(product_id, quantity_change, reason, user):
    """Manual Admin adjustment: positive adds stock, negative removes it."""
    with transaction.atomic():
        product = lock_products([product_id]).get(product_id)
        if product is None:
            raise NotFound("Product not found.")

        movement_type = (
            StockMovement.MovementType.ADJUSTMENT_IN
            if quantity_change > 0
            else StockMovement.MovementType.ADJUSTMENT_OUT
        )
        return change_stock(product, quantity_change, movement_type, user, reason)
