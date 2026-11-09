"""
Business rules for sales orders: create, edit (Draft only), confirm and
cancel. Views stay thin and call these functions.

Concurrency approach (pessimistic locking):
  1. Everything runs inside transaction.atomic(), so the status change,
     stock changes and stock movements are saved together or not at all.
  2. The order row is locked with SELECT ... FOR UPDATE. Two requests to
     confirm (or cancel) the same order queue up; the second one then sees
     the new status and is rejected, so stock is never moved twice.
  3. The product rows are locked (in id order, see inventory.services) before
     stock is checked. If two users confirm different orders for the same
     limited stock, the second waits, then reads the stock left after the
     first commit and is rejected if it is not enough.
  4. The database CHECK constraint (stock >= 0) is a final safety net.
"""

from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from core.exceptions import ConflictError
from core.permissions import is_admin
from inventory.models import StockMovement
from inventory.services import change_stock, lock_products

from .calculations import calculate_order_totals
from .models import SalesOrder, SalesOrderItem


# --------------------------------------------------------------------------
# Lookups and ownership
# --------------------------------------------------------------------------

def orders_visible_to(user):
    """Admin sees every order; a Sales User only sees orders they created."""
    queryset = SalesOrder.objects.select_related("customer", "created_by")
    if is_admin(user):
        return queryset
    return queryset.filter(created_by=user)


def get_order_for_user(order_id, user, lock=False):
    """
    Another user's order gives 404, exactly like an id that does not exist,
    so changing the id in the URL reveals nothing.
    """
    queryset = orders_visible_to(user)
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    try:
        return queryset.get(pk=order_id)
    except SalesOrder.DoesNotExist:
        raise NotFound("Order not found.")


# --------------------------------------------------------------------------
# Create / edit
# --------------------------------------------------------------------------

def create_order(*, user, customer, items, discount_percentage):
    with transaction.atomic():
        order = SalesOrder.objects.create(
            # temporary unique value; replaced below once the id is known
            order_number=f"TMP-{uuid4().hex[:20]}",
            customer=customer,
            discount_percentage=discount_percentage,
            created_by=user,
        )
        order.order_number = build_order_number(order)
        _save_items_and_totals(order, items, existing_rates={})
        return order


def update_draft_order(*, order_id, user, customer, items, discount_percentage):
    with transaction.atomic():
        order = get_order_for_user(order_id, user, lock=True)
        _ensure_draft(order, "edited")

        # Lines that stay on the order keep the rate stored when they were
        # added; only newly added products take the current product price.
        existing_rates = {item.product_id: item.rate for item in order.items.all()}
        order.items.all().delete()

        order.customer = customer
        order.discount_percentage = discount_percentage
        _save_items_and_totals(order, items, existing_rates)
        return order


def build_order_number(order):
    """e.g. SO-202611-00042. Built from the primary key, so it is always unique."""
    return f"SO-{order.order_date:%Y%m}-{order.pk:05d}"


def _save_items_and_totals(order, items, existing_rates):
    rates = [existing_rates.get(item["product"].pk, item["product"].price) for item in items]
    totals = calculate_order_totals(
        [(item["quantity"], rate) for item, rate in zip(items, rates)],
        order.discount_percentage,
    )

    SalesOrderItem.objects.bulk_create([
        SalesOrderItem(order=order, product=item["product"], quantity=item["quantity"], rate=rate, amount=amount)
        for item, rate, amount in zip(items, rates, totals.line_amounts)
    ])

    order.subtotal = totals.subtotal
    order.discount_amount = totals.discount_amount
    order.grand_total = totals.grand_total
    order.save()


# --------------------------------------------------------------------------
# Status changes
# --------------------------------------------------------------------------

def confirm_order(*, order_id, user):
    with transaction.atomic():
        order = get_order_for_user(order_id, user, lock=True)

        if order.status == SalesOrder.Status.CONFIRMED:
            raise ConflictError(f"Order {order.order_number} is already confirmed. Stock was not deducted again.")
        _ensure_draft(order, "confirmed")

        if not order.customer.is_active:
            raise ValidationError("This customer is inactive. Activate the customer before confirming the order.")

        items = list(order.items.all())
        if not items:
            raise ValidationError("An order needs at least one item before it can be confirmed.")

        products = lock_products([item.product_id for item in items])

        # Check every line first, so either all stock is deducted or none.
        problems = []
        for item in items:
            product = products[item.product_id]
            if not product.is_active:
                problems.append(f"{product.product_code} ({product.name}) is no longer active")
            elif product.stock_quantity < item.quantity:
                problems.append(
                    f"{product.product_code} ({product.name}): ordered {item.quantity}, "
                    f"only {product.stock_quantity} in stock"
                )
        if problems:
            raise ConflictError("Order cannot be confirmed. " + "; ".join(problems) + ".")

        for item in items:
            change_stock(
                products[item.product_id],
                -item.quantity,
                StockMovement.MovementType.SALE,
                user,
                reason=f"Order {order.order_number} confirmed",
                order=order,
            )

        order.status = SalesOrder.Status.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=["status", "confirmed_at", "updated_at"])
        return order


def cancel_order(*, order_id, user):
    with transaction.atomic():
        order = get_order_for_user(order_id, user, lock=True)

        if order.status == SalesOrder.Status.CANCELLED:
            raise ConflictError(f"Order {order.order_number} is already cancelled. Stock was not restored again.")

        if order.status == SalesOrder.Status.CONFIRMED:
            # Only a Confirmed order had stock deducted, so only it gets stock back.
            items = list(order.items.all())
            products = lock_products([item.product_id for item in items])
            for item in items:
                change_stock(
                    products[item.product_id],
                    item.quantity,
                    StockMovement.MovementType.SALE_REVERSAL,
                    user,
                    reason=f"Order {order.order_number} cancelled",
                    order=order,
                )

        order.status = SalesOrder.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.save(update_fields=["status", "cancelled_at", "updated_at"])
        return order


def _ensure_draft(order, action):
    if order.status != SalesOrder.Status.DRAFT:
        raise ConflictError(
            f"Order {order.order_number} is {order.get_status_display().lower()} and cannot be {action}. "
            "Only Draft orders can be changed."
        )
