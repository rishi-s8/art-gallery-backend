import logging
from collections import Counter
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from django.conf import settings
from celery import shared_task
from servers.models import Server
from .models import ServerAnalytics, RequestLog, NetworkAnalytics, ClientTrafficLog

logger = logging.getLogger('mcp_nexus')

@shared_task
def generate_daily_network_analytics():
    """
    Generate daily network analytics.
    """
    try:
        # Get yesterday's date
        yesterday = timezone.now().date() - timedelta(days=1)

        # Check if we already have analytics for yesterday
        if NetworkAnalytics.objects.filter(date=yesterday).exists():
            logger.info(f"Network analytics for {yesterday} already exist, skipping generation")
            return

        # Count servers
        all_servers = Server.objects.all()
        active_servers = all_servers.filter(is_active=True)
        total_servers = all_servers.count()
        active_count = active_servers.count()

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

        # Count new servers created yesterday
        new_servers = all_servers.filter(
            created_at__date=yesterday
        ).count()

        # Count requests made yesterday
        request_logs = RequestLog.objects.filter(
            timestamp__date=yesterday
        )
        total_requests = request_logs.count()

        # Count unique clients
        unique_clients = request_logs.values('client_id').distinct().count()

        # Get top tags
        tags_counter = Counter()
        for server in all_servers:
            for tag in server.tags:
                tags_counter[tag] += 1

        top_tags = {tag: count for tag, count in tags_counter.most_common(20)}

        # Create network analytics record
        NetworkAnalytics.objects.create(
            date=yesterday,
            total_servers=total_servers,
            active_servers=active_count,
            total_requests=total_requests,
            unique_clients=unique_clients,
            new_servers=new_servers,
            agent_count=agent_count,
            resource_count=resource_count,
            tool_count=tool_count,
            top_tags=top_tags
        )

        logger.info(f"Generated network analytics for {yesterday}")

    except Exception as e:
        logger.error(f"Error generating network analytics: {str(e)}", exc_info=True)


@shared_task
def clean_old_request_logs():
    """
    Clean up old request logs to manage database size.
    """
    try:
        # Calculate retention threshold
        retention_days = settings.ANALYTICS_RETENTION_DAYS
        threshold_date = timezone.now().date() - timedelta(days=retention_days)

        # Delete old logs
        old_logs = RequestLog.objects.filter(timestamp__date__lt=threshold_date)
        count = old_logs.count()
        old_logs.delete()

        logger.info(f"Cleaned {count} old request logs (older than {threshold_date})")

    except Exception as e:
        logger.error(f"Error cleaning old request logs: {str(e)}", exc_info=True)


@shared_task
def aggregate_client_analytics():
    """
    Aggregate client analytics to detect usage patterns.
    This task analyzes client behavior across servers.
    """
    try:
        # Get yesterday's date
        yesterday = timezone.now().date() - timedelta(days=1)

        # Find clients that used multiple servers
        multi_server_clients = ClientTrafficLog.objects.filter(
            date=yesterday,
        ).annotate(
            server_count=Count('servers_accessed')
        ).filter(
            server_count__gt=1
        )

        if multi_server_clients.exists():
            logger.info(f"Found {multi_server_clients.count()} clients using multiple servers on {yesterday}")

            # TODO: Implement further analysis and reporting

    except Exception as e:
        logger.error(f"Error aggregating client analytics: {str(e)}", exc_info=True)