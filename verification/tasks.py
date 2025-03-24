import logging
import requests
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from servers.models import Server
from .models import VerificationRequest, HealthCheck

logger = logging.getLogger('mcp_nexus')

@shared_task
def initiate_verification(server_id):
    """
    Initiate the verification process for a newly registered server.
    """
    try:
        server = Server.objects.get(id=server_id)

        # Check if server exists and is accessible
        try:
            response = requests.get(f"{server.url.rstrip('/')}/health", timeout=5)
            is_up = response.status_code == 200
            response_time = response.elapsed.total_seconds()
        except Exception as e:
            logger.error(f"Error checking server health during initiation: {str(e)}", exc_info=True)
            is_up = False
            response_time = 0

        # Record health check
        HealthCheck.objects.create(
            server=server,
            is_up=is_up,
            response_time=response_time,
            details={"check_type": "initial_verification"}
        )

        # If server is up, update status to active
        if is_up:
            server.is_active = True
            server.status_message = "Server is active"
            server.save()
        else:
            server.is_active = False
            server.status_message = "Server is not responding"
            server.save()

        logger.info(f"Initiated verification for server: {server.name} (ID: {server.id})")

    except Server.DoesNotExist:
        logger.error(f"Server not found for verification initiation: {server_id}")
    except Exception as e:
        logger.error(f"Error during verification initiation: {str(e)}", exc_info=True)


@shared_task
def check_server_health(server_id):
    """
    Check the health of a server and update its status.
    """
    try:
        server = Server.objects.get(id=server_id)

        try:
            # Check if server is up
            response = requests.get(f"{server.url.rstrip('/')}/health", timeout=5)
            is_up = response.status_code == 200
            response_time = response.elapsed.total_seconds()
            status_code = response.status_code
            error_message = None
        except requests.RequestException as e:
            is_up = False
            response_time = 0
            status_code = None
            error_message = str(e)

        # Record health check
        HealthCheck.objects.create(
            server=server,
            is_up=is_up,
            response_time=response_time,
            status_code=status_code,
            error_message=error_message,
            details={"check_type": "scheduled"}
        )

        logger.info(f"Health check for server {server.name}: {'UP' if is_up else 'DOWN'}")

    except Server.DoesNotExist:
        logger.error(f"Server not found for health check: {server_id}")
    except Exception as e:
        logger.error(f"Error during server health check: {str(e)}", exc_info=True)


@shared_task
def run_scheduled_health_checks():
    """
    Run health checks for all active servers on a schedule.
    """
    # Get all active servers that haven't been checked in the check interval
    check_cutoff = timezone.now() - settings.VERIFICATION_CHECK_INTERVAL
    servers_to_check = Server.objects.filter(
        is_active=True,
        last_checked__lt=check_cutoff
    )

    logger.info(f"Running scheduled health checks for {servers_to_check.count()} servers")

    for server in servers_to_check:
        check_server_health.delay(str(server.id))