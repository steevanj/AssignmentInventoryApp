from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer


class CurrentUserView(APIView):
    """Lets the frontend find out who is logged in (and their role) on page load."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)
