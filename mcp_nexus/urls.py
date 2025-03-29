from django.contrib import admin
from django.urls import URLResolver, path, include, URLPattern
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

api_v1_patterns = [
    path('auth/', include('authentication.urls')),
    path('servers/', include('servers.urls')),
    path('discovery/', include('discovery.urls')),
    path('verification/', include('verification.urls')),
    path('analytics/', include('analytics.urls')),
    path('webhooks/', include('webhooks.urls')),
]

urlpatterns: list[URLPattern | URLResolver] = [
    path('admin/', admin.site.urls),

    # API v1 URLs
    path('api/v1/', include(api_v1_patterns)),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]