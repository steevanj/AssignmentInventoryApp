import re

from rest_framework import serializers

from .models import Customer

MOBILE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "mobile", "city", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"name": {"error_messages": {"blank": "Customer name is required."}}}

    def validate_mobile(self, value):
        value = value.replace(" ", "").replace("-", "")
        if value and not MOBILE_PATTERN.match(value):
            raise serializers.ValidationError("Enter a valid mobile number (7 to 15 digits, optional leading +).")
        return value

    def validate_email(self, value):
        return value.lower()
