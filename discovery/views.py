from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, fields
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework import status, views, generics, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from servers.models import Server
from .models import SearchHistory, ServerUsage, UserPreference
from .serializers import (
    SearchHistorySerializer,
    ServerUsageSerializer,
    ServerUsageCreateSerializer,
    UserPreferenceSerializer,
    ServerSearchResultSerializer,
    SearchParamsSerializer,
    ServerRecommendationSerializer,
    PopularServersParamsSerializer
)

class SearchView(views.APIView):
    """
    API view for searching MCP servers.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Search for MCP servers",
        description="Advanced semantic search for discovering MCP servers based on capabilities, functionality, and other criteria.",
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
            OpenApiParameter(name='type', description='Filter by server type', required=False, type=str),
            OpenApiParameter(name='tags', description='Filter by tags (comma-separated)', required=False, type=str),
            OpenApiParameter(name='verified', description='Filter by verification status', required=False, type=bool),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Results per page', required=False, type=int),
        ],
        responses={200: ServerSearchResultSerializer(many=True)}
    )
    def get(self, request):
        # Validate search parameters
        serializer = SearchParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Get search parameters
        query = serializer.validated_data.get('q')
        server_type = serializer.validated_data.get('type')
        tags = serializer.validated_data.get('tags')
        verified = serializer.validated_data.get('verified')

        # Start with all servers
        queryset = Server.objects.all()

        # Apply filters
        if server_type:
            queryset = queryset.filter(types__contains=[server_type])

        if tags:
            tag_list = tags.split(',')
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag.strip()])

        if verified is not None:
            queryset = queryset.filter(verified=verified)

        # Perform full-text search
        search_vector = SearchVector('name', weight='A') + \
                       SearchVector('description', weight='B') + \
                       SearchVector('provider', weight='C') + \
                       SearchVector('tags', weight='D')

        search_query = SearchQuery(query)

        queryset = queryset.annotate(
            search=search_vector,
            relevance_score=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-relevance_score')

        # Extract highlights
        highlight_fields = ['description']
        for server in queryset:
            server.highlight = {}
            for field in highlight_fields:
                text = getattr(server, field)
                # Simple highlight implementation - in production, use a more sophisticated method
                if text and query.lower() in text.lower():
                    start = max(0, text.lower().find(query.lower()) - 50)
                    end = min(len(text), text.lower().find(query.lower()) + len(query) + 50)
                    highlighted = f"...{text[start:end]}..."
                    server.highlight[field] = highlighted

        # Record search in history if user is authenticated
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=query,
                filters={
                    'type': server_type,
                    'tags': tags,
                    'verified': verified
                },
                results_count=queryset.count()
            )

        # Paginate results
        from common.pagination import StandardResultsSetPagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ServerSearchResultSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = ServerSearchResultSerializer(queryset, many=True, context={'request': request})
        return Response({'data': serializer.data})


class RecommendationsView(views.APIView):
    """
    API view for getting personalized server recommendations.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get server recommendations",
        description="Get personalized recommendations for MCP servers based on usage history, preferences, and popularity.",
        parameters=[
            OpenApiParameter(name='type', description='Filter by server type', required=False, type=str),
            OpenApiParameter(name='limit', description='Maximum number of recommendations', required=False, type=int),
        ],
        responses={200: ServerRecommendationSerializer(many=True)}
    )
    def get(self, request):
        # Get parameters
        server_type = request.query_params.get('type')
        limit = int(request.query_params.get('limit', 5))

        # Get user preferences
        try:
            preferences = UserPreference.objects.get(user=request.user)
        except UserPreference.DoesNotExist:
            preferences = UserPreference.objects.create(user=request.user)

        # Get servers the user has interacted with
        used_server_ids = ServerUsage.objects.filter(
            user=request.user
        ).values_list('server_id', flat=True).distinct()

        # Get servers with the same tags as the user's preferred tags
        tag_based = []
        if preferences.preferred_tags:
            tag_query = Q()
            for tag in preferences.preferred_tags:
                tag_query |= Q(tags__contains=[tag])

            tag_based = Server.objects.filter(tag_query)

            if server_type:
                tag_based = tag_based.filter(types__contains=[server_type])

            # Exclude servers the user has already used
            tag_based = tag_based.exclude(id__in=used_server_ids)

            # Exclude servers the user has explicitly excluded
            tag_based = tag_based.exclude(id__in=preferences.excluded_servers.all())

            # Annotate with recommendation reason
            for server in tag_based:
                server.recommendation_reason = "Based on your preferred tags"

        # Get popular servers the user hasn't used yet
        popular = Server.objects.order_by('-usage_count')

        if server_type:
            popular = popular.filter(types__contains=[server_type])

        # Exclude servers the user has already used
        popular = popular.exclude(id__in=used_server_ids)

        # Exclude servers the user has explicitly excluded
        popular = popular.exclude(id__in=preferences.excluded_servers.all())

        # Annotate with recommendation reason
        for server in popular:
            server.recommendation_reason = "Popular among users"

        # Combine recommendations, prioritizing tag-based
        recommendations = list(tag_based)

        # Add popular servers until we reach the limit
        for server in popular:
            if len(recommendations) >= limit:
                break
            if server not in recommendations:
                recommendations.append(server)

        # Limit to requested number
        recommendations = recommendations[:limit]

        serializer = ServerRecommendationSerializer(recommendations, many=True, context={'request': request})
        return Response({'data': serializer.data})


class PopularServersView(views.APIView):
    """
    API view for getting popular MCP servers.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get popular MCP servers",
        description="Get a list of popular MCP servers based on usage statistics and ratings.",
        parameters=[
            OpenApiParameter(name='type', description='Filter by server type', required=False, type=str),
            OpenApiParameter(name='period', description='Time period for popularity calculation', required=False, type=str, enum=['day', 'week', 'month', 'all_time']),
            OpenApiParameter(name='limit', description='Maximum number of servers to return', required=False, type=int),
        ],
        responses={200: ServerSearchResultSerializer(many=True)}
    )
    def get(self, request):
        # Validate parameters
        serializer = PopularServersParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Get parameters
        server_type = serializer.validated_data.get('type')
        period = serializer.validated_data.get('period', 'week')
        limit = serializer.validated_data.get('limit', 10)

        # Start with all servers
        queryset = Server.objects.all()

        # Apply type filter if provided
        if server_type:
            queryset = queryset.filter(types__contains=[server_type])

        # Calculate popularity based on usage and ratings for the specified period
        if period != 'all_time':
            period_start = None
            if period == 'day':
                period_start = timezone.now() - timedelta(days=1)
            elif period == 'week':
                period_start = timezone.now() - timedelta(days=7)
            elif period == 'month':
                period_start = timezone.now() - timedelta(days=30)

            # Get usage counts for the period
            recent_usage = ServerUsage.objects.filter(
                created_at__gte=period_start
            ).values('server').annotate(
                recent_count=Count('id')
            )

            # Create a mapping of server_id to recent usage count
            usage_dict = {u['server']: u['recent_count'] for u in recent_usage}

            # Annotate servers with their recent usage count
            for server in queryset:
                server.recent_usage = usage_dict.get(server.id, 0)

            # Sort by recent usage and rating
            queryset = sorted(
                queryset,
                key=lambda s: (s.recent_usage, s.rating),
                reverse=True
            )
        else:
            # For all time, sort by total usage count and rating
            queryset = queryset.order_by('-usage_count', '-rating')

        # Limit to requested number
        queryset = queryset[:limit]

        serializer = ServerSearchResultSerializer(queryset, many=True, context={'request': request})
        return Response({'data': serializer.data})


class SearchHistoryView(generics.ListAPIView):
    """
    API view for viewing a user's search history.
    """
    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)


class ServerUsageHistoryView(generics.ListAPIView):
    """
    API view for viewing a user's server usage history.
    """
    serializer_class = ServerUsageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServerUsage.objects.filter(user=self.request.user)


class ServerUsageCreateView(generics.CreateAPIView):
    """
    API view for recording server usage.
    """
    serializer_class = ServerUsageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """
    API view for managing user preferences.
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get or create user preferences."""
        try:
            return UserPreference.objects.get(user=self.request.user)
        except UserPreference.DoesNotExist:
            return UserPreference.objects.create(user=self.request.user)