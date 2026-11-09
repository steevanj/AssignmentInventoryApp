from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Email is the login id, so users are created with email + password."""

    use_in_migrations = True

    def create_user(self, email, password=None, name="", role=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        user = self.model(
            email=self.normalize_email(email).lower(),
            name=name,
            role=role or self.model.Role.SALES,
            **extra_fields,
        )
        user.set_password(password)  # stores a salted PBKDF2 hash, never the raw password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, name="", **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, name=name, role=self.model.Role.ADMIN, **extra_fields)
