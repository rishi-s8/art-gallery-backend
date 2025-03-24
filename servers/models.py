import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify

User = get_user_model()

class Server(models.Model):
    """
    Model representing an MCP server registered in the system.
    """
    SERVER_TYPE_CHOICES = [
        ('agent', 'Agent'),
        ('resource', 'Resource'),
        ('tool', 'Tool'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    provider = models.CharField(max_length=255)

    url = models.URLField()
    documentation_url = models.URLField(blank=True, null=True)

    types = ArrayField(
        models.CharField(max_length=10, choices=SERVER_TYPE_CHOICES),
        default=list
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )

    logo = models.ImageField(upload_to='server_logos/', blank=True, null=True)

    # The user who registered the server
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_servers')

    # Server verification status
    verified = models.BooleanField(default=False)

    # Rating and usage stats
    rating = models.FloatField(default=0.0)
    uptime = models.FloatField(default=100.0)  # Percentage
    usage_count = models.PositiveIntegerField(default=0)

    # Metadata
    version = models.CharField(max_length=50, blank=True, null=True)
    protocols = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )

    # Status info
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now_add=True)
    status_message = models.CharField(max_length=255, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Generate a slug from the name if one isn't provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner']),
            models.Index(fields=['verified']),
            models.Index(fields=['created_at']),
        ]


class ServerCapability(models.Model):
    """
    Model representing a capability of an MCP server.
    """
    CAPABILITY_TYPE_CHOICES = [
        ('agent', 'Agent'),
        ('resource', 'Resource'),
        ('tool', 'Tool'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='capabilities')

    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=10, choices=CAPABILITY_TYPE_CHOICES)

    examples = ArrayField(
        models.TextField(),
        blank=True,
        default=list
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.server.name} - {self.name}"

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['server', 'name']),
            models.Index(fields=['type']),
        ]
        unique_together = ['server', 'name']


class CapabilityParameter(models.Model):
    """
    Model representing a parameter for an MCP server capability.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capability = models.ForeignKey(ServerCapability, on_delete=models.CASCADE, related_name='parameters')

    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=50)
    required = models.BooleanField(default=False)
    default = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.capability.name} - {self.name}"

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['capability']),
        ]
        unique_together = ['capability', 'name']


class UsageRequirements(models.Model):
    """
    Model representing the usage requirements for an MCP server.
    """
    AUTH_TYPE_CHOICES = [
        ('none', 'None'),
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth 2.0'),
        ('jwt', 'JWT'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.OneToOneField(Server, on_delete=models.CASCADE, related_name='usage_requirements')

    authentication_required = models.BooleanField(default=False)
    authentication_type = models.CharField(max_length=10, choices=AUTH_TYPE_CHOICES, default='none')
    rate_limits = models.CharField(max_length=255, blank=True, null=True)
    pricing = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.server.name} - Usage Requirements"


class ServerRating(models.Model):
    """
    Model representing a user rating of an MCP server.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_ratings')

    rating = models.IntegerField()  # Rating from 1 to 5
    review = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.server.name} - {self.user.email} - {self.rating}"

    def save(self, *args, **kwargs):
        """Update the server's average rating when a new rating is added."""
        super().save(*args, **kwargs)

        # Update the server's average rating
        ratings = self.server.ratings.all()
        if ratings.exists():
            self.server.rating = sum([r.rating for r in ratings]) / ratings.count()
            self.server.save(update_fields=['rating'])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
        ]
        unique_together = ['server', 'user']