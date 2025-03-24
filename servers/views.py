from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Server, ServerRating
from .serializers import (
    ServerSummarySerializer,
    ServerRegistrationSerializer,
    ServerUpdateSerializer,
    ServerDetailSerializer,
    ServerRatingSerializer,
    ServerRatingCreateSerializer
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a server to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user

@extend_schema_view(
    list=extend_schema(
        summary="List servers",
        description="Get a paginated list of all registered MCP servers."
    ),
    retrieve=extend_schema(
        summary="Get server details",
        description="Get detailed information about a specific MCP server."
    ),
    create=extend_schema(
        summary="Register server",
        description="Register a new MCP server in the decentralized registry."
    ),
    update=extend_schema(
        summary="Update server",
        description="Update the details of an existing MCP server."
    ),
    partial_update=extend_schema(
        summary="Partially update server",
        description="Partially update the details of an existing MCP server."
    ),
    destroy=extend_schema(
        summary="Delete server",
        description="Remove an MCP server from the registry."
    )
)
class ServerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing server instances.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['types', 'tags', 'verified']
    search_fields = ['name', 'description', 'provider', 'tags']
    ordering_fields = ['name', 'created_at', 'rating', 'uptime']
    ordering = ['-created_at']
    lookup_field = 'id'

    def get_permissions(self):
        """
        Custom permissions:
        - Create: Must be authenticated
        - Update/Delete: Must be owner
        - List/Retrieve: Any user can access
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter servers based on query parameters:
        - type: Filter by server type
        - tags: Filter by tags
        - verified: Filter by verification status
        - search: Search by name, description, provider, and tags
        """
        queryset = Server.objects.all()

        # Get query parameters
        server_type = self.request.query_params.get('type')
        tags = self.request.query_params.get('tags')
        verified = self.request.query_params.get('verified')

        # Apply filters
        if server_type:
            queryset = queryset.filter(types__contains=[server_type])

        if tags:
            tag_list = tags.split(',')
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag.strip()])

        if verified:
            verified_bool = verified.lower() == 'true'
            queryset = queryset.filter(verified=verified_bool)

        return queryset

    def get_serializer_class(self):
        """
        Return different serializers based on the action:
        - list: ServerSummarySerializer
        - retrieve: ServerDetailSerializer
        - create: ServerRegistrationSerializer
        - update/partial_update: ServerUpdateSerializer
        """
        if self.action == 'list':
            return ServerSummarySerializer
        elif self.action == 'retrieve':
            return ServerDetailSerializer
        elif self.action == 'create':
            return ServerRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
            return ServerUpdateSerializer
        return ServerDetailSerializer

    def perform_create(self, serializer):
        """Create a new server and perform initial verification checks."""
        serializer.save()

        # Trigger verification task asynchronously
        from verification.tasks import initiate_verification
        server = serializer.instance
        initiate_verification.delay(str(server.id))

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def ratings(self, request, id=None):
        """
        Get all ratings for a specific server.
        """
        server = self.get_object()
        ratings = server.ratings.all()

        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = ServerRatingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ServerRatingSerializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, id=None):
        """
        Rate a server (create or update a rating).
        """
        server = self.get_object()
        serializer = ServerRatingCreateSerializer(
            data=request.data,
            context={'request': request, 'server': server}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly])
    def activate(self, request, id=None):
        """
        Activate a server that is currently inactive.
        """
        server = self.get_object()

        if server.is_active:
            return Response(
                {"message": "Server is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        server.is_active = True
        server.status_message = "Activated by owner"
        server.save()

        # Trigger verification
        from verification.tasks import check_server_health
        check_server_health.delay(str(server.id))

        return Response({"message": "Server activated"})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly])
    def deactivate(self, request, id=None):
        """
        Deactivate a server temporarily.
        """
        server = self.get_object()

        if not server.is_active:
            return Response(
                {"message": "Server is already inactive"},
                status=status.HTTP_400_BAD_REQUEST
            )

        server.is_active = False
        server.status_message = request.data.get('message', "Deactivated by owner")
        server.save()

        return Response({"message": "Server deactivated"})

class UserServerListView(generics.ListAPIView):
    """
    API view to list servers owned by the current user.
    """
    serializer_class = ServerSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return servers owned by the current user."""
        return Server.objects.filter(owner=self.request.user)