from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebhookViewSet,
    WebhookDeliveryDetailView,
    WebhookDeliveryRetryView,
    WebhookTestView
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'', WebhookViewSet, basename='webhook')

urlpatterns = [
    path('deliveries/<uuid:delivery_id>/', WebhookDeliveryDetailView.as_view(), name='webhook-delivery-detail'),
    path('deliveries/<uuid:delivery_id>/retry/', WebhookDeliveryRetryView.as_view(), name='webhook-delivery-retry'),
    path('<uuid:webhook_id>/test/', WebhookTestView.as_view(), name='webhook-test'),
    path('', include(router.urls)),
]