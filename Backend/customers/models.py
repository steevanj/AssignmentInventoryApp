from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            # the search box looks up name / email / mobile, the list filters on status
            models.Index(fields=["name"], name="customer_name_idx"),
            models.Index(fields=["email"], name="customer_email_idx"),
            models.Index(fields=["mobile"], name="customer_mobile_idx"),
            models.Index(fields=["is_active"], name="customer_active_idx"),
        ]

    def __str__(self):
        return self.name
