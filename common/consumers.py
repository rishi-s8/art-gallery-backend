import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

class StatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time status updates.
    """

    async def connect(self):
        """
        Connect to the WebSocket and join the status group.
        """
        # Join the status group
        await self.channel_layer.group_add(
            "status_updates",
            self.channel_name
        )

        await self.accept()

        # Send initial status
        await self.send_status()

    async def disconnect(self, close_code):
        """
        Leave the status group when disconnecting.
        """
        await self.channel_layer.group_discard(
            "status_updates",
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'get_status':
                await self.send_status()

        except json.JSONDecodeError:
            pass

    async def status_update(self, event):
        """
        Receive status update from group and send to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))

    async def send_status(self):
        """
        Send current system status to the WebSocket.
        """
        status = await self.get_system_status()

        await self.send(text_data=json.dumps({
            'type': 'status',
            'data': status
        }))

    @database_sync_to_async
    def get_system_status(self):
        """
        Get the current system status.
        """
        from servers.models import Server
        from verification.models import HealthCheck

        # Get basic system stats
        total_servers = Server.objects.count()
        active_servers = Server.objects.filter(is_active=True).count()
        verified_servers = Server.objects.filter(verified=True).count()

        # Get server types
        server_types = {'agent': 0, 'resource': 0, 'tool': 0}
        for server in Server.objects.all():
            for server_type in server.types:
                if server_type in server_types:
                    server_types[server_type] += 1

        # Get recent health checks
        recent_checks = HealthCheck.objects.order_by('-created_at')[:100]
        health_status = {
            'healthy': recent_checks.filter(is_up=True).count(),
            'unhealthy': recent_checks.filter(is_up=False).count(),
            'avg_response_time': sum(check.response_time for check in recent_checks) / max(1, len(recent_checks))
        }

        return {
            'servers': {
                'total': total_servers,
                'active': active_servers,
                'verified': verified_servers,
                'types': server_types
            },
            'health': health_status,
            'api_version': settings.REST_FRAMEWORK.get('DEFAULT_VERSION', 'v1'),
            'timestamp': 'timestamp'  # Will be filled in by JavaScript
        }