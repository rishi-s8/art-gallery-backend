from rest_framework import serializers
from django.utils.text import slugify
from .models import Server, ServerCapability, CapabilityParameter, UsageRequirements, ServerRating

class CapabilityParameterSerializer(serializers.ModelSerializer):
    """Serializer for capability parameters."""
    class Meta:
        model = CapabilityParameter
        fields = ['name', 'description', 'type', 'required', 'default']

class ServerCapabilitySerializer(serializers.ModelSerializer):
    """Serializer for server capabilities."""
    parameters = CapabilityParameterSerializer(many=True, required=False)

    class Meta:
        model = ServerCapability
        fields = ['name', 'description', 'type', 'parameters', 'examples']

    def create(self, validated_data):
        """Create capability with nested parameters."""
        parameters_data = validated_data.pop('parameters', [])
        capability = ServerCapability.objects.create(**validated_data)

        for param_data in parameters_data:
            CapabilityParameter.objects.create(capability=capability, **param_data)

        return capability

class UsageRequirementsSerializer(serializers.ModelSerializer):
    """Serializer for server usage requirements."""
    class Meta:
        model = UsageRequirements
        fields = ['authentication_required', 'authentication_type', 'rate_limits', 'pricing']

class ServerRatingSerializer(serializers.ModelSerializer):
    """Serializer for server ratings."""
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = ServerRating
        fields = ['id', 'rating', 'review', 'user_email', 'created_at']
        read_only_fields = ['id', 'user_email', 'created_at']

    def get_user_email(self, obj):
        """Get the email of the user who created the rating."""
        return obj.user.email

class ServerSummarySerializer(serializers.ModelSerializer):
    """Serializer for server summaries (used in list views)."""
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'slug', 'description', 'provider', 'types',
            'tags', 'verified', 'created_at', 'updated_at', 'logo_url',
            'rating', 'uptime', 'url', 'documentation_url'
        ]
        read_only_fields = ['id', 'verified', 'created_at', 'updated_at', 'rating', 'uptime']

    def get_logo_url(self, obj):
        """Get the URL of the server logo."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None

class ServerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for server registration."""
    capabilities = ServerCapabilitySerializer(many=True, required=False)
    usage_requirements = UsageRequirementsSerializer(required=False)
    contact_email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        model = Server
        fields = [
            'name', 'slug', 'description', 'provider', 'url', 'documentation_url',
            'types', 'tags', 'logo', 'capabilities', 'protocols', 'usage_requirements',
            'contact_email'
        ]
        extra_kwargs = {
            'slug': {'required': False},
        }

    def validate_url(self, value):
        """Validate that the URL is a valid MCP server."""
        from common.utils import validate_mcp_server_url

        valid, response = validate_mcp_server_url(value)
        if not valid:
            raise serializers.ValidationError(f"URL does not point to a valid MCP server: {response['error']}")
        return value

    def create(self, validated_data):
        """Create a server with nested capabilities and usage requirements."""
        contact_email = validated_data.pop('contact_email', None)
        capabilities_data = validated_data.pop('capabilities', [])
        usage_requirements_data = validated_data.pop('usage_requirements', None)

        # Generate slug if not provided
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])

        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user

        # Create the server
        server = Server.objects.create(**validated_data)

        # Create capabilities
        for capability_data in capabilities_data:
            parameters_data = capability_data.pop('parameters', [])
            capability = ServerCapability.objects.create(server=server, **capability_data)

            for param_data in parameters_data:
                CapabilityParameter.objects.create(capability=capability, **param_data)

        # Create usage requirements
        if usage_requirements_data:
            UsageRequirements.objects.create(server=server, **usage_requirements_data)

        return server

class ServerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing server."""
    capabilities = ServerCapabilitySerializer(many=True, required=False)
    usage_requirements = UsageRequirementsSerializer(required=False)
    contact_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Server
        fields = [
            'name', 'description', 'url', 'documentation_url', 'types',
            'tags', 'logo', 'capabilities', 'protocols', 'usage_requirements',
            'contact_email'
        ]

    def update(self, instance, validated_data):
        """Update a server with nested capabilities and usage requirements."""
        capabilities_data = validated_data.pop('capabilities', None)
        usage_requirements_data = validated_data.pop('usage_requirements', None)

        # Update the server fields
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        # Update capabilities if provided
        if capabilities_data is not None:
            # Delete existing capabilities
            instance.capabilities.all().delete()

            # Create new capabilities
            for capability_data in capabilities_data:
                parameters_data = capability_data.pop('parameters', [])
                capability = ServerCapability.objects.create(server=instance, **capability_data)

                for param_data in parameters_data:
                    CapabilityParameter.objects.create(capability=capability, **param_data)

        # Update usage requirements if provided
        if usage_requirements_data is not None:
            if hasattr(instance, 'usage_requirements'):
                # Update existing usage requirements
                for key, value in usage_requirements_data.items():
                    setattr(instance.usage_requirements, key, value)
                instance.usage_requirements.save()
            else:
                # Create new usage requirements
                UsageRequirements.objects.create(server=instance, **usage_requirements_data)

        return instance

class ServerDetailSerializer(serializers.ModelSerializer):
    """Serializer for server details."""
    capabilities = ServerCapabilitySerializer(many=True, read_only=True)
    usage_requirements = UsageRequirementsSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Server
        fields = [
            'id', 'name', 'slug', 'description', 'provider', 'url', 'documentation_url',
            'types', 'tags', 'logo_url', 'verified', 'rating', 'uptime', 'usage_count',
            'version', 'capabilities', 'protocols', 'usage_requirements', 'owner_email',
            'is_active', 'last_checked', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_logo_url(self, obj):
        """Get the URL of the server logo."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None

    def get_owner_email(self, obj):
        """Get the email of the server owner."""
        # Only return the owner email if the request user is the owner
        request = self.context.get('request')
        if request and request.user == obj.owner:
            return obj.owner.email
        return None

    def get_status(self, obj):
        """Get server status information."""
        return {
            'is_active': obj.is_active,
            'last_checked': obj.last_checked,
            'message': obj.status_message
        }

class ServerRatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating server ratings."""
    class Meta:
        model = ServerRating
        fields = ['rating', 'review']

    def validate_rating(self, value):
        """Validate that the rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def create(self, validated_data):
        """Create a rating, or update if one already exists from this user."""
        server = self.context['server']
        user = self.context['request'].user

        # Check if the user has already rated this server
        try:
            rating = ServerRating.objects.get(server=server, user=user)
            # Update existing rating
            for key, value in validated_data.items():
                setattr(rating, key, value)
            rating.save()
        except ServerRating.DoesNotExist:
            # Create new rating
            rating = ServerRating.objects.create(server=server, user=user, **validated_data)

        return rating