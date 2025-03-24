from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServerViewSet, UserServerListView

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', ServerViewSet, basename='server')

urlpatterns = [
    path('me/', UserServerListView.as_view(), name='user-servers'),
    path('', include(router.urls)),
]