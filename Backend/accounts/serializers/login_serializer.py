from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import User


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ["email", "password"]
        # The model's unique validator would reject an email that already
        # exists, which is the opposite of what a login form needs.
        extra_kwargs = {"email": {"validators": []}}

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].strip().lower(),
            password=attrs["password"],
        )
        if user is None:
            # Same message for "no such user", "wrong password" and "inactive"
            # so the response does not reveal which emails are registered.
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs
