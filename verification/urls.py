from django.urls import path
from .views import (
    RequestVerificationView,
    VerificationStatusView,
    CompleteVerificationView,
    VerificationBadgeView,
    HealthCheckListView
)

urlpatterns = [
    path('request/<uuid:server_id>/', RequestVerificationView.as_view(), name='request-verification'),
    path('status/<uuid:verification_id>/', VerificationStatusView.as_view(), name='verification-status'),
    path('complete/<uuid:verification_id>/', CompleteVerificationView.as_view(), name='complete-verification'),
    path('badge/<uuid:server_id>/', VerificationBadgeView.as_view(), name='verification-badge'),
    path('health-checks/<uuid:server_id>/', HealthCheckListView.as_view(), name='health-checks'),
]