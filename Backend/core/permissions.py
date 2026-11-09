from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user):
    """Single place that decides whether a user has the Admin role."""
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "ADMIN")


class IsAdminRole(BasePermission):
    message = "Only Admin users can perform this action."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Any logged-in user can read; only Admin users can create, edit or delete."""

    message = "Only Admin users can change master data."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user)
