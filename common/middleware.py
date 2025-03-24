import json
import logging
import time
import uuid
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger('mcp_nexus')

class RequestLoggingMiddleware:
    """
    Middleware to log all requests and responses.
    Also adds a request_id to the request to track requests through the system.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        self.log_request(request)

        # Process request
        response = self.get_response(request)

        # Calculate request time
        request_time = time.time() - start_time

        # Log response
        self.log_response(request, response, request_time)

        # Add request ID to response headers
        response['X-Request-ID'] = request_id

        return response

    def log_request(self, request):
        """Log request details"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', None),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'remote_addr': self.get_client_ip(request),
            'user_id': request.user.id if request.user.is_authenticated else None,
        }

        # Only log request body in debug mode
        if settings.DEBUG and request.body:
            try:
                log_data['body'] = json.loads(request.body)
            except json.JSONDecodeError:
                log_data['body'] = str(request.body)

        logger.info(f"Request: {json.dumps(log_data, default=str)}")

    def log_response(self, request, response, request_time):
        """Log response details"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', None),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time': round(request_time * 1000, 2),  # in milliseconds
        }

        # Only log response content in debug mode and if it's JSON
        if settings.DEBUG and hasattr(response, 'content'):
            content_type = response.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    log_data['response'] = json.loads(response.content)
                except json.JSONDecodeError:
                    pass

        logger.info(f"Response: {json.dumps(log_data, default=str)}")

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip