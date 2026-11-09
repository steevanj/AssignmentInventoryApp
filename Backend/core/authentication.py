from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """
    Same as DRF's SessionAuthentication, but makes unauthenticated
    requests return 401 Unauthorized instead of 403 Forbidden.

    DRF only sends 401 when the first authentication class provides a
    WWW-Authenticate header value. Plain session auth does not, so every
    "not logged in" error would otherwise look like a permission error.
    """

    def authenticate_header(self, request):
        return 'Session realm="api"'
