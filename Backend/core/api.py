"""Small helpers shared by the APIViews (query params, filtering, pagination)."""

from datetime import date

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from .pagination import StandardPagination
from .permissions import is_admin

STATUS_FILTER_VALUES = ("active", "inactive", "all")


def paginated_response(request, queryset, serializer_class, view):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request, view=view)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def apply_active_filter(queryset, request):
    """
    ?status=active|inactive|all for Admin users (default: active).
    Sales Users only ever see active records, whatever they ask for.
    """
    if not is_admin(request.user):
        return queryset.filter(is_active=True)

    status = request.query_params.get("status", "active").strip().lower() or "active"
    if status not in STATUS_FILTER_VALUES:
        raise ValidationError({"status": "Use one of: active, inactive, all."})
    if status == "active":
        return queryset.filter(is_active=True)
    if status == "inactive":
        return queryset.filter(is_active=False)
    return queryset


def parse_date_param(request, name):
    raw = request.query_params.get(name, "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValidationError({name: "Enter a valid date in YYYY-MM-DD format."})


def parse_date_range(request):
    date_from = parse_date_param(request, "date_from")
    date_to = parse_date_param(request, "date_to")
    if date_from and date_to and date_from > date_to:
        raise ValidationError({"date_to": "End date cannot be before the start date."})
    return date_from, date_to


def parse_int_param(request, name, *, required=False, min_value=None):
    raw = request.query_params.get(name, "").strip()
    if not raw:
        if required:
            raise ValidationError({name: "This parameter is required."})
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError({name: "Enter a whole number."})
    if min_value is not None and value < min_value:
        raise ValidationError({name: f"Must be {min_value} or more."})
    return value


class ApiNotFoundView(APIView):
    """Catch-all so unknown /api/ URLs get a JSON 404 instead of an HTML page."""

    authentication_classes = []
    permission_classes = []

    def initial(self, request, *args, **kwargs):
        raise NotFound("This API endpoint does not exist.")
