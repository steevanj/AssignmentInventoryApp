from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ConflictError
from core.permissions import IsAdminOrReadOnly, is_admin
from products.models import Product
from products.serializers import ProductSerializer, ProductUpdateSerializer


class ProductDetailView(APIView):
    """
    GET    /api/products/<id>/
    PUT    /api/products/<id>/   Admin. stock_quantity is ignored, use a stock adjustment.
    PATCH  /api/products/<id>/   Admin.
    DELETE /api/products/<id>/   Admin. Only if no order item or stock movement uses it.
    """

    permission_classes = [IsAdminOrReadOnly]

    def get_product(self, request, pk):
        queryset = Product.objects.all()
        if not is_admin(request.user):
            queryset = queryset.filter(is_active=True)
        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk):
        return Response(ProductSerializer(self.get_product(request, pk)).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def delete(self, request, pk):
        product = self.get_product(request, pk)
        if product.order_items.exists() or product.stock_movements.exists():
            raise ConflictError(
                "This product is used in orders or has stock history and cannot be deleted. "
                "Mark it inactive instead."
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update(self, request, pk, partial):
        product = self.get_product(request, pk)
        serializer = ProductUpdateSerializer(product, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
