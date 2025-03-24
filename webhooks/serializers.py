from rest_framework import serializers
from .models import Webhook, WebhookDelivery

class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for webhook configurations."""
    class Meta:
        model = Webhook
        fields = [
            'id', 'url', 'events', 'description', 'active',
            'secret', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'secret', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create webhook with the current user as owner."""
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)


class WebhookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating webhooks."""
    class Meta:
        model = Webhook
        fields = ['url', 'events', 'description']


class WebhookUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating webhooks."""
    class Meta:
        model = Webhook
        fields = ['url', 'events', 'active', 'description']

    def validate_events(self, value):
        """Validate that events are from the allowed choices."""
        valid_events = [choice[0] for choice in Webhook.EVENT_CHOICES]
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(
                    f"Invalid event: {event}. Valid events are: {', '.join(valid_events)}"
                )
        return value


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for webhook delivery records."""
    webhook_url = serializers.CharField(source='webhook.url', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'webhook', 'webhook_url', 'event', 'payload',
            'status', 'attempt_count', 'response_code', 'response_body',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class WebhookDeliveryDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed webhook delivery information."""
    webhook_url = serializers.CharField(source='webhook.url', read_only=True)
    webhook_events = serializers.ListField(source='webhook.events', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'webhook', 'webhook_url', 'webhook_events', 'event',
            'payload', 'status', 'attempt_count', 'response_code',
            'response_body', 'created_at', 'updated_at'
        ]
        read_only_fields = fields