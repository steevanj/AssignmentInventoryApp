import logging

from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ConflictError(APIException):
    """Request is valid, but clashes with the current state of a record."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the record."
    default_code = "conflict"


def api_exception_handler(exc, context):
    """
    Turns every error into a predictable JSON shape:

        {"error": "Human readable message", "details": {...optional...}}

    Unexpected exceptions are logged with their traceback on the server and
    the client only gets a generic message, so internals never leak out.
    """
    if isinstance(exc, ProtectedError):
        return Response(
            {"error": "This record is used by other records and cannot be deleted. "
                      "Mark it inactive instead."},
            status=status.HTTP_409_CONFLICT,
        )

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled error in %s", context.get("view"))
        return Response(
            {"error": "Something went wrong on the server. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        response.data = _format_validation_error(response.data)
    elif isinstance(exc, Http404):
        response.data = {"error": "The requested record was not found."}
    else:
        detail = response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data
        response.data = {"error": str(detail)}

    return response


def _format_validation_error(data):
    """
    Plain business-rule errors (raised as a single message) become a simple
    {"error": "..."}; field level errors keep their per-field "details" so
    the frontend can show them next to the right input.
    """
    if isinstance(data, list):
        return {"error": " ".join(str(message) for message in data)}
    if isinstance(data, dict) and set(data) == {"non_field_errors"}:
        return {"error": " ".join(str(message) for message in data["non_field_errors"])}
    return {"error": "Please correct the highlighted fields.", "details": data}
