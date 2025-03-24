import logging
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions, viewsets, generics, views
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Webhook, WebhookDelivery
from .serializers import (
    WebhookSerializer,
    WebhookCreateSerializer,
    WebhookUpdateSerializer,
    WebhookDeliverySerializer,
    WebhookDeliveryDetailSerializer
)

logger = logging.getLogger('mcp_nexus')

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a webhook to view and edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_staff:
            return True

        # Allow webhook owner
        return obj.owner == request.user

@extend_schema_view(
    list=extend_schema(
        summary="List webhooks",
        description="Get a list of all webhooks configured by the current user."
    ),
    retrieve=extend_schema(
        summary="Get webhook details",
        description="Get detailed information about a specific webhook."
    ),
    create=extend_schema(
        summary="Create webhook",
        description="Create a new webhook for event notifications."
    ),
    update=extend_schema(
        summary="Update webhook",
        description="Update an existing webhook configuration."
    ),
    partial_update=extend_schema(
        summary="Partially update webhook",
        description="Partially update an existing webhook configuration."
    ),
    destroy=extend_schema(
        summary="Delete webhook",
        description="Delete a webhook configuration."
    ),
    regenerate_secret=extend_schema(
        summary="Regenerate webhook secret",
        description="Generate a new secret for signing webhook payloads."
    ),
    deliveries=extend_schema(
        summary="List webhook deliveries",
        description="Get a list of delivery attempts for a specific webhook."
    )
)
class WebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing webhook configurations.
    """
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return webhooks owned by the current user."""
        return Webhook.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        """Return different serializers based on the action."""
        if self.action == 'create':
            return WebhookCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WebhookUpdateSerializer
        return WebhookSerializer

    @action(detail=True, methods=['post'])
    def regenerate_secret(self, request, pk=None):
        """
        Regenerate the secret for a webhook.
        """
        webhook = self.get_object()

        # Clear secret to trigger automatic regeneration
        webhook.secret = ''
        webhook.save()

        return Response({
            'id': webhook.id,
            'secret': webhook.secret
        })

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """
        Get delivery history for a webhook.
        """
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()

        page = self.paginate_queryset(deliveries)
        if page is not None:
            serializer = WebhookDeliverySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


class WebhookDeliveryDetailView(generics.RetrieveAPIView):
    """
    API view for detailed webhook delivery information.
    """
    serializer_class = WebhookDeliveryDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return deliveries for webhooks owned by the current user."""
        return WebhookDelivery.objects.filter(webhook__owner=self.request.user)


class WebhookDeliveryRetryView(views.APIView):
    """
    API view for retrying a failed webhook delivery.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(
        summary="Retry webhook delivery",
        description="Retry a failed webhook delivery attempt.",
        responses={
            202: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
            404: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def post(self, request, *args, **kwargs):
        # Get the delivery
        delivery_id = kwargs.get('delivery_id')
        delivery = get_object_or_404(
            WebhookDelivery,
            id=delivery_id,
            webhook__owner=request.user
        )

        # Check if the delivery is in a failed state
        if delivery.status != 'failed':
            return Response(
                {"error": f"Cannot retry delivery with status: {delivery.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if webhook is active
        if not delivery.webhook.active:
            return Response(
                {"error": "Cannot retry delivery for inactive webhook"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Queue delivery for retry
        from .tasks import retry_webhook_delivery
        retry_webhook_delivery.delay(str(delivery.id))

        return Response(
            {"message": "Webhook delivery queued for retry"},
            status=status.HTTP_202_ACCEPTED
        )


class WebhookTestView(views.APIView):
    """
    API view for testing a webhook configuration.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(
        summary="Test webhook",
        description="Send a test event to a webhook to verify it's working correctly.",
        responses={
            202: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
            404: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def post(self, request, *args, **kwargs):
        # Get the webhook
        webhook_id = kwargs.get('webhook_id')
        webhook = get_object_or_404(
            Webhook,
            id=webhook_id,
            owner=request.user
        )

        # Check if webhook is active
        if not webhook.active:
            return Response(
                {"error": "Cannot test inactive webhook"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a test payload
        test_payload = {
            "event": "webhook.test",
            "webhook_id": str(webhook.id),
            "timestamp": "2023-01-01T00:00:00Z",
            "data": {
                "message": "This is a test webhook event"
            }
        }

        # Create a delivery record
        delivery = WebhookDelivery.objects.create(
            webhook=webhook,
            event="webhook.test",
            payload=test_payload,
            status="pending"
        )

        # Queue delivery
        from .tasks import process_webhook_delivery
        process_webhook_delivery.delay(str(delivery.id))

        return Response(
            {
                "message": "Test webhook delivery queued",
                "delivery_id": str(delivery.id)
            },
            status=status.HTTP_202_ACCEPTED
        )