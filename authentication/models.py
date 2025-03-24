import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model that uses email as the unique identifier instead of username."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    organization = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_expiry = models.DateTimeField(null=True, blank=True)

    # API Key for authentication to the MCP Nexus API
    api_key = models.CharField(max_length=64, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def generate_api_key(self):
        """Generate a new API key for the user."""
        import secrets
        self.api_key = secrets.token_hex(32)
        self.save()
        return self.api_key

    def verify_email(self):
        """Mark the user's email as verified."""
        self.is_verified = True
        self.verification_token = None
        self.verification_token_expiry = None
        self.save()

    def generate_verification_token(self):
        """Generate a verification token for email verification."""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expiry = timezone.now() + timezone.timedelta(days=2)
        self.save()
        return self.verification_token

    def is_verification_token_valid(self):
        """Check if the verification token is still valid."""
        if not self.verification_token or not self.verification_token_expiry:
            return False
        return timezone.now() < self.verification_token_expiry