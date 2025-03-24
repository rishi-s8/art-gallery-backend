from rest_framework import serializers
from servers.models import Server
from servers.serializers import ServerSummarySerializer
from .models import SearchHistory, ServerUsage, UserPreference

class SearchHistorySerializer(serializers.ModelSerializer):
    """Serializer for search history records."""
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'filters', 'results_count', 'created_at']
        read_only_fields = fields

class ServerUsageSerializer(serializers.ModelSerializer):
    """Serializer for server usage records."""
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = ServerUsage
        fields = ['id', 'server', 'server_name', 'capability', 'parameters', 
                  'successful', 'response_time', 'created_at']
        read_only_fields = ['id', 'created_at']

class ServerUsageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating server usage records."""
    class Meta:
        model = ServerUsage
        fields = ['server', 'capability', 'parameters', 'successful', 'response_time']

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences."""
    class Meta:
        model = UserPreference
        fields = ['preferred_types', 'preferred_tags', 'excluded_servers']

class ServerSearchResultSerializer(ServerSummarySerializer):
    """Serializer for search results, extending the summary serializer with relevance info."""
    relevance_score = serializers.FloatField(read_only=True)
    highlight = serializers.DictField(read_only=True)
    
    class Meta(ServerSummarySerializer.Meta):
        fields = ServerSummarySerializer.Meta.fields + ['relevance_score', 'highlight']

class SearchParamsSerializer(serializers.Serializer):
    """Serializer for search parameters."""
    q = serializers.CharField(required=True, help_text="Search query")
    type = serializers.CharField(required=False, help_text="Filter by server type")
    tags = serializers.CharField(required=False, help_text="Filter by tags (comma-separated)")
    verified = serializers.BooleanField(required=False, help_text="Filter by verification status")

class ServerRecommendationSerializer(ServerSummarySerializer):
    """Serializer for server recommendations."""
    recommendation_reason = serializers.CharField(read_only=True)
    
    class Meta(ServerSummarySerializer.Meta):
        fields = ServerSummarySerializer.Meta.fields + ['recommendation_reason']

class PopularServersParamsSerializer(serializers.Serializer):
    """Serializer for popular servers request parameters."""
    type = serializers.CharField(required=False, help_text="Filter by server type")
    period = serializers.ChoiceField(
        choices=['day', 'week', 'month', 'all_time'],
        default='week',
        help_text="Time period for popularity calculation"
    )
    limit = serializers.IntegerField(
        min_value=1,
        max_value=50,
        default=10,
        help_text="Maximum number of servers to return"
    )