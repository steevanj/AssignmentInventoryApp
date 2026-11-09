"""
Two users confirm different orders for the same limited stock at the same
moment. Uses real threads with their own DB connections, so it needs MySQL
(SQLite ignores SELECT ... FOR UPDATE) and a TransactionTestCase (data must
be committed so the other connection can see it).
"""

import threading
import unittest

from django.db import connection
from django.test import TransactionTestCase

from core.factories import make_customer, make_product, make_user
from inventory.models import StockMovement
from orders import services
from orders.models import SalesOrder


@unittest.skipUnless(connection.vendor == "mysql", "Row locking test needs MySQL.")
class ConcurrentConfirmationTests(TransactionTestCase):
    def test_two_users_cannot_oversell_limited_stock(self):
        product = make_product("LIM-1", stock=5)
        customer = make_customer()
        user_a, user_b = make_user(), make_user()
        order_a = services.create_order(user=user_a, customer=customer,
                                        items=[{"product": product, "quantity": 4}], discount_percentage=0)
        order_b = services.create_order(user=user_b, customer=customer,
                                        items=[{"product": product, "quantity": 4}], discount_percentage=0)

        start_together = threading.Barrier(2)
        outcomes = []

        def confirm(order, user):
            start_together.wait()
            try:
                services.confirm_order(order_id=order.pk, user=user)
                outcomes.append("confirmed")
            except Exception:
                outcomes.append("rejected")
            finally:
                connection.close()

        threads = [threading.Thread(target=confirm, args=(order_a, user_a)),
                   threading.Thread(target=confirm, args=(order_b, user_b))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        product.refresh_from_db()
        self.assertEqual(sorted(outcomes), ["confirmed", "rejected"])
        self.assertEqual(product.stock_quantity, 1)
        self.assertEqual(SalesOrder.objects.filter(status="CONFIRMED").count(), 1)
        self.assertEqual(StockMovement.objects.filter(movement_type="SALE").count(), 1)
