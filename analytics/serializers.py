from rest_framework import serializers
from .models import ServerAnalytics, RequestLog, NetworkAnalytics, ClientTrafficLog

class TimeSeriesPointSerializer(serializers.Serializer):
    """Serializer for time series data points."""
    timestamp = serializers.DateTimeField()
    count = serializers.IntegerField(required=False)
    avg_ms = serializers.FloatField(required=False)

class TopItemSerializer(serializers.Serializer):
    """Serializer for top items with counts and percentages."""
    name = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()

class MetricsSerializer(serializers.Serializer):
    """Serializer for analytics metrics."""
    total_requests = serializers.IntegerField()
    unique_clients = serializers.IntegerField()
    avg_response_time_ms = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime_percentage = serializers.FloatField()

class ServerAnalyticsSerializer(serializers.Serializer):
    """Serializer for server analytics."""
    server_id = serializers.UUIDField()
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year', 'custom'])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    metrics = MetricsSerializer()
    
    time_series = serializers.Serializer(
        requests=TimeSeriesPointSerializer(many=True),
        response_times=TimeSeriesPointSerializer(many=True),
        errors=TimeSeriesPointSerializer(many=True)
    )
    
    top_clients = TopItemSerializer(many=True)
    top_capabilities = TopItemSerializer(many=True)

class RequestLogSerializer(serializers.ModelSerializer):
    """Serializer for request logs."""
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = RequestLog
        fields = [
            'id', 'server', 'server_name', 'client_id', 'timestamp', 'capability',
            'status_code', 'response_time_ms', 'is_error', 'error_details',
            'country_code'
        ]
        read_only_fields = ['id', 'server_name', 'timestamp']

class RequestLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating request logs."""
    class Meta:
        model = RequestLog
        fields = [
            'server', 'client_id', 'capability', 'status_code', 'response_time_ms',
            'user_agent', 'ip_address', 'request_headers', 'request_body',
            'is_error', 'error_details'
        ]
    
    def create(self, validated_data):
        """Create request log with current timestamp."""
        from django.utils import timezone
        validated_data['timestamp'] = timezone.now()
        
        # Determine if request is an error based on status code
        if 'status_code' in validated_data and validated_data['status_code']:
            status_code = validated_data['status_code']
            validated_data['is_error'] = status_code >= 400
        
        return super().create(validated_data)

class NetworkAnalyticsSerializer(serializers.Serializer):
    """Serializer for network analytics."""
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year'])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    metrics = serializers.Serializer(
        total_servers=serializers.IntegerField(),
        active_servers=serializers.IntegerField(),
        total_requests=serializers.IntegerField(),
        unique_clients=serializers.IntegerField(),
        new_servers=serializers.IntegerField()
    )
    
    server_types = serializers.Serializer(
        agents=serializers.IntegerField(),
        resources=serializers.IntegerField(),
        tools=serializers.IntegerField()
    )
    
    top_tags = TopItemSerializer(many=True)
    
    time_series = serializers.Serializer(
        servers=TimeSeriesPointSerializer(many=True),
        requests=TimeSeriesPointSerializer(many=True)
    )

class DailyServerAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for daily server analytics records."""
    server_name = serializers.CharField(source='server.name', read_only=True)
    error_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ServerAnalytics
        fields = [
            'id', 'server', 'server_name', 'date', 'total_requests',
            'unique_clients', 'avg_response_time_ms', 'error_count',
            'error_rate', 'status_2xx', 'status_3xx', 'status_4xx',
            'status_5xx', 'top_capabilities'
        ]
        read_only_fields = ['id', 'server_name', 'error_rate']

class ClientTrafficLogSerializer(serializers.ModelSerializer):
    """Serializer for client traffic logs."""
    class Meta:
        model = ClientTrafficLog
        fields = [
            'id', 'client_id', 'date', 'servers_accessed',
            'total_requests', 'top_capabilities', 'country_code'
        ]
        read_only_fields = ['id']