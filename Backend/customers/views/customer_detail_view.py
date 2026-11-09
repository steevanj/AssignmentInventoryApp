from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ConflictError
from core.permissions import IsAdminOrReadOnly, is_admin
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerDetailView(APIView):
    """
    GET    /api/customers/<id>/   view
    PUT    /api/customers/<id>/   full update (Admin)
    PATCH  /api/customers/<id>/   partial update, e.g. {"is_active": false} (Admin)
    DELETE /api/customers/<id>/   delete, only if no order uses the customer (Admin)
    """

    permission_classes = [IsAdminOrReadOnly]

    def get_customer(self, request, pk):
        queryset = Customer.objects.all()
        if not is_admin(request.user):
            queryset = queryset.filter(is_active=True)
        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk):
        return Response(CustomerSerializer(self.get_customer(request, pk)).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def delete(self, request, pk):
        customer = self.get_customer(request, pk)
        if customer.orders.exists():
            raise ConflictError(
                "This customer has sales orders and cannot be deleted. Mark the customer inactive instead."
            )
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request, pk, partial):
        customer = self.get_customer(request, pk)
        serializer = CustomerSerializer(customer, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
