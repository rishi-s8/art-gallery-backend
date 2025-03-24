from django.urls import path
from .views import (
    ServerAnalyticsView,
    NetworkAnalyticsView,
    RequestLogListView,
    RequestLogCreateView,
    DailyAnalyticsListView
)

urlpatterns = [
    path('servers/<uuid:server_id>/', ServerAnalyticsView.as_view(), name='server-analytics'),
    path('network/', NetworkAnalyticsView.as_view(), name='network-analytics'),
    path('servers/<uuid:server_id>/logs/', RequestLogListView.as_view(), name='server-logs'),
    path('servers/<uuid:server_id>/daily/', DailyAnalyticsListView.as_view(), name='daily-analytics'),
    path('log/', RequestLogCreateView.as_view(), name='create-log'),
]