from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public view of a user. The password hash is never included."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "role_display"]
        read_only_fields = fields
