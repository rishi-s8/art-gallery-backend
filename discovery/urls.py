from django.urls import path
from .views import (
    SearchView,
    RecommendationsView,
    PopularServersView,
    SearchHistoryView,
    ServerUsageHistoryView,
    ServerUsageCreateView,
    UserPreferenceView
)

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('recommend/', RecommendationsView.as_view(), name='recommend'),
    path('popular/', PopularServersView.as_view(), name='popular'),
    path('history/search/', SearchHistoryView.as_view(), name='search-history'),
    path('history/usage/', ServerUsageHistoryView.as_view(), name='usage-history'),
    path('usage/', ServerUsageCreateView.as_view(), name='record-usage'),
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
]