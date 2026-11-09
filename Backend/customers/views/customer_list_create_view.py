from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import apply_active_filter, paginated_response
from core.permissions import IsAdminOrReadOnly
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerListCreateView(APIView):
    """
    GET  /api/customers/?search=&status=&page=   list (Sales Users: active only)
    POST /api/customers/                         create (Admin only)
    """

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        queryset = Customer.objects.all()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(mobile__icontains=search)
            )

        queryset = apply_active_filter(queryset, request)
        return paginated_response(request, queryset, CustomerSerializer, self)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
