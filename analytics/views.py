from datetime import timedelta
from collections import Counter
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Sum, F, Q
from rest_framework import status, permissions, generics, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from servers.models import Server
from servers.views import IsOwnerOrReadOnly
from discovery.models import ServerUsage
from .models import ServerAnalytics, RequestLog, NetworkAnalytics, ClientTrafficLog
from .serializers import (
    ServerAnalyticsSerializer,
    RequestLogSerializer,
    RequestLogCreateSerializer,
    NetworkAnalyticsSerializer,
    DailyServerAnalyticsSerializer,
    ClientTrafficLogSerializer
)

class ServerAnalyticsView(views.APIView):
    """
    API view for retrieving server analytics.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @extend_schema(
        summary="Get server analytics",
        description="Retrieve usage analytics for a specific MCP server.",
        parameters=[
            OpenApiParameter(name='period', description='Time period for analytics', required=False, type=str, enum=['day', 'week', 'month', 'year']),
            OpenApiParameter(name='start_date', description='Start date for custom time range (ISO format)', required=False, type=str, format='date'),
            OpenApiParameter(name='end_date', description='End date for custom time range (ISO format)', required=False, type=str, format='date'),
        ],
        responses={200: ServerAnalyticsSerializer}
    )
    def get(self, request, *args, **kwargs):
        # Get the server
        server_id = kwargs.get('server_id')
        server = get_object_or_404(Server, id=server_id)

        # Check if the user is the server owner
        self.check_object_permissions(request, server)

        # Get date range parameters
        period = request.query_params.get('period', 'month')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Calculate date range
        if start_date and end_date:
            # Custom date range
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                period = 'custom'
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Predefined period
            today = timezone.now().date()
            if period == 'day':
                start_date = today - timedelta(days=1)
                end_date = today
            elif period == 'week':
                start_date = today - timedelta(days=7)
                end_date = today
            elif period == 'month':
                start_date = today - timedelta(days=30)
                end_date = today
            elif period == 'year':
                start_date = today - timedelta(days=365)
                end_date = today
            else:
                return Response(
                    {"error": "Invalid period. Use 'day', 'week', 'month', 'year', or provide 'start_date' and 'end_date'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Get analytics data from models
        daily_analytics = ServerAnalytics.objects.filter(
            server=server,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        request_logs = RequestLog.objects.filter(
            server=server,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )

        # If no data, return empty response with the date range
        if not daily_analytics.exists() and not request_logs.exists():
            return Response({
                'server_id': str(server.id),
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': {
                    'total_requests': 0,
                    'unique_clients': 0,
                    'avg_response_time_ms': 0,
                    'error_rate': 0,
                    'uptime_percentage': server.uptime
                },
                'time_series': {
                    'requests': [],
                    'response_times': [],
                    'errors': []
                },
                'top_clients': [],
                'top_capabilities': []
            })

        # Calculate metrics
        total_requests = sum(day.total_requests for day in daily_analytics)
        unique_clients = sum(day.unique_clients for day in daily_analytics)

        # If no analytics but have request logs, calculate from logs
        if not daily_analytics.exists():
            total_requests = request_logs.count()
            unique_clients = request_logs.values('client_id').distinct().count()

        # Calculate average response time
        if daily_analytics.exists():
            # Weighted average based on request count
            total_weighted_time = sum(day.avg_response_time_ms * day.total_requests for day in daily_analytics)
            avg_response_time = total_weighted_time / total_requests if total_requests > 0 else 0
        else:
            avg_response_time = request_logs.aggregate(avg=Avg('response_time_ms'))['avg'] or 0

        # Calculate error rate
        if daily_analytics.exists():
            total_errors = sum(day.error_count for day in daily_analytics)
        else:
            total_errors = request_logs.filter(is_error=True).count()

        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Build time series data
        time_series_requests = []
        time_series_response_times = []
        time_series_errors = []

        for day in daily_analytics:
            time_series_requests.append({
                'timestamp': day.date.isoformat(),
                'count': day.total_requests
            })
            time_series_response_times.append({
                'timestamp': day.date.isoformat(),
                'avg_ms': day.avg_response_time_ms
            })
            time_series_errors.append({
                'timestamp': day.date.isoformat(),
                'count': day.error_count
            })

        # If no daily analytics, create time series from logs
        if not daily_analytics.exists() and request_logs.exists():
            # Group logs by day
            from django.db.models.functions import TruncDate
            requests_by_day = request_logs.annotate(
                day=TruncDate('timestamp')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            response_times_by_day = request_logs.annotate(
                day=TruncDate('timestamp')
            ).values('day').annotate(
                avg_ms=Avg('response_time_ms')
            ).order_by('day')

            errors_by_day = request_logs.filter(
                is_error=True
            ).annotate(
                day=TruncDate('timestamp')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            for item in requests_by_day:
                time_series_requests.append({
                    'timestamp': item['day'].isoformat(),
                    'count': item['count']
                })

            for item in response_times_by_day:
                time_series_response_times.append({
                    'timestamp': item['day'].isoformat(),
                    'avg_ms': item['avg_ms']
                })

            for item in errors_by_day:
                time_series_errors.append({
                    'timestamp': item['day'].isoformat(),
                    'count': item['count']
                })

        # Get top clients
        if request_logs.exists():
            client_counts = request_logs.values('client_id').annotate(
                count=Count('id')
            ).order_by('-count')[:10]

            total_logs = request_logs.count()
            top_clients = [
                {
                    'name': item['client_id'] or 'Anonymous',
                    'count': item['count'],
                    'percentage': (item['count'] / total_logs * 100) if total_logs > 0 else 0
                }
                for item in client_counts if item['client_id']
            ]
        else:
            top_clients = []

        # Get top capabilities
        if request_logs.exists():
            capability_counts = request_logs.values('capability').annotate(
                count=Count('id')
            ).order_by('-count')[:10]

            total_logs = request_logs.count()
            top_capabilities = [
                {
                    'name': item['capability'] or 'Unknown',
                    'count': item['count'],
                    'percentage': (item['count'] / total_logs * 100) if total_logs > 0 else 0
                }
                for item in capability_counts if item['capability']
            ]
        else:
            # Try to get capabilities from daily analytics
            top_capabilities = []
            if daily_analytics.exists() and daily_analytics.first().top_capabilities:
                cap_data = daily_analytics.first().top_capabilities
                for cap_name, cap_count in cap_data.items():
                    top_capabilities.append({
                        'name': cap_name,
                        'count': cap_count,
                        'percentage': (cap_count / total_requests * 100) if total_requests > 0 else 0
                    })

        # Build response
        response_data = {
            'server_id': str(server.id),
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metrics': {
                'total_requests': total_requests,
                'unique_clients': unique_clients,
                'avg_response_time_ms': avg_response_time,
                'error_rate': error_rate,
                'uptime_percentage': server.uptime
            },
            'time_series': {
                'requests': time_series_requests,
                'response_times': time_series_response_times,
                'errors': time_series_errors
            },
            'top_clients': top_clients,
            'top_capabilities': top_capabilities
        }

        return Response(response_data)


class NetworkAnalyticsView(views.APIView):
    """
    API view for retrieving network-wide analytics.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get network analytics",
        description="Retrieve analytics about the overall MCP Nexus network.",
        parameters=[
            OpenApiParameter(name='period', description='Time period for analytics', required=False, type=str, enum=['day', 'week', 'month', 'year']),
        ],
        responses={200: NetworkAnalyticsSerializer}
    )
    def get(self, request):
        # Get period parameter
        period = request.query_params.get('period', 'month')

        # Calculate date range
        today = timezone.now().date()
        if period == 'day':
            start_date = today - timedelta(days=1)
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == 'year':
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            return Response(
                {"error": "Invalid period. Use 'day', 'week', 'month', or 'year'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get network analytics data
        network_analytics = NetworkAnalytics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        # If no data, generate from servers and logs
        if not network_analytics.exists():
            # Count servers
            all_servers = Server.objects.all()
            active_servers = all_servers.filter(is_active=True)

            # Count servers by type
            agent_count = 0
            resource_count = 0
            tool_count = 0

            for server in all_servers:
                if 'agent' in server.types:
                    agent_count += 1
                if 'resource' in server.types:
                    resource_count += 1
                if 'tool' in server.types:
                    tool_count += 1

            # Count new servers
            new_servers = all_servers.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()

            # Count requests
            total_requests = RequestLog.objects.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            ).count()

            # Count unique clients
            unique_clients = RequestLog.objects.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            ).values('client_id').distinct().count()

            # Get top tags
            tags_counter = Counter()
            for server in all_servers:
                for tag in server.tags:
                    tags_counter[tag] += 1

            top_tags = [
                {
                    'name': tag,
                    'count': count,
                    'percentage': (count / all_servers.count() * 100) if all_servers.count() > 0 else 0
                }
                for tag, count in tags_counter.most_common(10)
            ]

            # Build time series
            servers_time_series = []
            requests_time_series = []

            # For servers, show cumulative count over time
            date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

            for date in date_range:
                servers_up_to_date = all_servers.filter(created_at__date__lte=date).count()
                servers_time_series.append({
                    'timestamp': date.isoformat(),
                    'count': servers_up_to_date
                })

            # For requests, group by day
            from django.db.models.functions import TruncDate
            requests_by_day = RequestLog.objects.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            ).annotate(
                day=TruncDate('timestamp')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            for item in requests_by_day:
                requests_time_series.append({
                    'timestamp': item['day'].isoformat(),
                    'count': item['count']
                })

            # Build response
            response_data = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': {
                    'total_servers': all_servers.count(),
                    'active_servers': active_servers.count(),
                    'total_requests': total_requests,
                    'unique_clients': unique_clients,
                    'new_servers': new_servers
                },
                'server_types': {
                    'agents': agent_count,
                    'resources': resource_count,
                    'tools': tool_count
                },
                'top_tags': top_tags,
                'time_series': {
                    'servers': servers_time_series,
                    'requests': requests_time_series
                }
            }

            return Response(response_data)

        # Build response from NetworkAnalytics records
        total_servers = network_analytics.order_by('-date').first().total_servers
        active_servers = network_analytics.order_by('-date').first().active_servers

        total_requests = sum(day.total_requests for day in network_analytics)
        unique_clients = sum(day.unique_clients for day in network_analytics)
        new_servers = sum(day.new_servers for day in network_analytics)

        # Latest server type counts
        latest = network_analytics.order_by('-date').first()
        agent_count = latest.agent_count
        resource_count = latest.resource_count
        tool_count = latest.tool_count

        # Top tags from the latest record
        top_tags = []
        if latest.top_tags:
            for tag_name, tag_count in latest.top_tags.items():
                top_tags.append({
                    'name': tag_name,
                    'count': tag_count,
                    'percentage': (tag_count / total_servers * 100) if total_servers > 0 else 0
                })

        # Build time series
        servers_time_series = []
        requests_time_series = []

        for day in network_analytics:
            servers_time_series.append({
                'timestamp': day.date.isoformat(),
                'count': day.total_servers
            })
            requests_time_series.append({
                'timestamp': day.date.isoformat(),
                'count': day.total_requests
            })

        # Build response
        response_data = {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metrics': {
                'total_servers': total_servers,
                'active_servers': active_servers,
                'total_requests': total_requests,
                'unique_clients': unique_clients,
                'new_servers': new_servers
            },
            'server_types': {
                'agents': agent_count,
                'resources': resource_count,
                'tools': tool_count
            },
            'top_tags': top_tags,
            'time_series': {
                'servers': servers_time_series,
                'requests': requests_time_series
            }
        }

        return Response(response_data)


class RequestLogListView(generics.ListAPIView):
    """
    API view for listing request logs for a server.
    """
    serializer_class = RequestLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        server_id = self.kwargs.get('server_id')
        server = get_object_or_404(Server, id=server_id)

        # Check if the user is the server owner
        self.check_object_permissions(self.request, server)

        return RequestLog.objects.filter(server=server).order_by('-timestamp')


class RequestLogCreateView(generics.CreateAPIView):
    """
    API view for logging requests.
    """
    serializer_class = RequestLogCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Create request log and update daily analytics."""
        log = serializer.save()

        # Get or create daily analytics record
        today = timezone.now().date()
        daily_analytics, created = ServerAnalytics.objects.get_or_create(
            server=log.server,
            date=today,
            defaults={
                'total_requests': 0,
                'unique_clients': 0,
                'avg_response_time_ms': 0,
                'error_count': 0,
                'status_2xx': 0,
                'status_3xx': 0,
                'status_4xx': 0,
                'status_5xx': 0,
                'top_capabilities': {}
            }
        )

        # Update analytics
        daily_analytics.total_requests += 1

        # Update unique clients
        if log.client_id:
            # Check if this client already made requests today
            client_exists = RequestLog.objects.filter(
                server=log.server,
                client_id=log.client_id,
                timestamp__date=today
            ).exclude(id=log.id).exists()

            if not client_exists:
                daily_analytics.unique_clients += 1

        # Update response time
        if daily_analytics.total_requests == 1:
            # First request of the day
            daily_analytics.avg_response_time_ms = log.response_time_ms
        else:
            # Update weighted average
            current_total = daily_analytics.avg_response_time_ms * (daily_analytics.total_requests - 1)
            new_avg = (current_total + log.response_time_ms) / daily_analytics.total_requests
            daily_analytics.avg_response_time_ms = new_avg

        # Update error count
        if log.is_error:
            daily_analytics.error_count += 1

        # Update status code counts
        if log.status_code:
            if 200 <= log.status_code < 300:
                daily_analytics.status_2xx += 1
            elif 300 <= log.status_code < 400:
                daily_analytics.status_3xx += 1
            elif 400 <= log.status_code < 500:
                daily_analytics.status_4xx += 1
            elif 500 <= log.status_code < 600:
                daily_analytics.status_5xx += 1

        # Update top capabilities
        if log.capability:
            capabilities = daily_analytics.top_capabilities
            capabilities[log.capability] = capabilities.get(log.capability, 0) + 1
            daily_analytics.top_capabilities = capabilities

        # Save analytics
        daily_analytics.save()

        # Update client traffic log
        if log.client_id:
            client_traffic, created = ClientTrafficLog.objects.get_or_create(
                client_id=log.client_id,
                date=today,
                defaults={
                    'servers_accessed': [str(log.server.id)],
                    'total_requests': 1,
                    'top_capabilities': {log.capability: 1} if log.capability else {},
                    'country_code': log.country_code
                }
            )

            if not created:
                # Update existing record
                client_traffic.total_requests += 1

                # Add server to accessed list if not already there
                server_id_str = str(log.server.id)
                if server_id_str not in client_traffic.servers_accessed:
                    client_traffic.servers_accessed.append(server_id_str)

                # Update capabilities
                if log.capability:
                    capabilities = client_traffic.top_capabilities
                    capabilities[log.capability] = capabilities.get(log.capability, 0) + 1
                    client_traffic.top_capabilities = capabilities

                client_traffic.save()


class DailyAnalyticsListView(generics.ListAPIView):
    """
    API view for listing daily analytics for a server.
    """
    serializer_class = DailyServerAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        server_id = self.kwargs.get('server_id')
        server = get_object_or_404(Server, id=server_id)

        # Check if the user is the server owner
        self.check_object_permissions(self.request, server)

        # Get date range from query params
        days = int(self.request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)

        return ServerAnalytics.objects.filter(
            server=server,
            date__gte=start_date
        ).order_by('-date')