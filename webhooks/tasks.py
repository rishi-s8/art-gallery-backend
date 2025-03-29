import logging
import json
import hmac
import hashlib
import time
import requests
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from .models import Webhook, WebhookDelivery

logger = logging.getLogger('mcp_nexus')

def sign_payload(payload, secret):
    """
    Create a signature for a webhook payload.
    """
    key = secret.encode('utf-8')
    message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature

@shared_task(bind=True, max_retries=3)
def process_webhook_delivery(self, delivery_id):
    """
    Process a webhook delivery.
    """
    try:
        delivery = WebhookDelivery.objects.get(id=delivery_id)
        webhook = delivery.webhook

        # Check if webhook is still active
        if not webhook.active:
            delivery.status = 'failed'
            delivery.response_body = 'Webhook is inactive'
            delivery.save()
            logger.info(f"Skipped delivery {delivery_id} to inactive webhook {webhook.id}")
            return

        # Increment attempt count
        delivery.attempt_count += 1
        delivery.save()

        # Prepare headers with signature
        signature = sign_payload(delivery.payload, webhook.secret)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MCP-Nexus-Webhook/1.0',
            'X-MCP-Nexus-Event': delivery.event,
            'X-MCP-Nexus-Delivery': str(delivery.id),
            'X-MCP-Nexus-Signature': f'sha256={signature}',
            'X-MCP-Nexus-Timestamp': str(int(time.time()))
        }

        # Send the webhook
        start_time = time.time()
        try:
            response = requests.post(
                webhook.url,
                headers=headers,
                json=delivery.payload,
                timeout=10
            )

            # Record response
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response size

            # Check if successful (2xx status)
            if 200 <= response.status_code < 300:
                delivery.status = 'success'
                logger.info(f"Webhook delivery {delivery_id} succeeded with status {response.status_code}")
            else:
                delivery.status = 'failed'
                logger.warning(f"Webhook delivery {delivery_id} failed with status {response.status_code}")

                # Retry for 5xx errors
                if response.status_code >= 500 and delivery.attempt_count < 3:
                    raise self.retry(countdown=60 * (2 ** (delivery.attempt_count - 1)))

        except requests.RequestException as e:
            delivery.status = 'failed'
            delivery.response_body = str(e)
            logger.error(f"Webhook delivery {delivery_id} failed: {str(e)}")

            # Retry on connection errors
            if delivery.attempt_count < 3:
                raise self.retry(countdown=60 * (2 ** (delivery.attempt_count - 1)))

        finally:
            # Save delivery record
            delivery.save()

    except WebhookDelivery.DoesNotExist:
        logger.error(f"Webhook delivery {delivery_id} not found")
    except Exception as e:
        logger.error(f"Error processing webhook delivery {delivery_id}: {str(e)}", exc_info=True)


@shared_task
def retry_webhook_delivery(delivery_id):
    """
    Retry a failed webhook delivery.
    """
    try:
        delivery = WebhookDelivery.objects.get(id=delivery_id, status='failed')
        process_webhook_delivery.delay(str(delivery.id))
        logger.info(f"Queued webhook delivery {delivery_id} for retry")
    except WebhookDelivery.DoesNotExist:
        logger.error(f"Failed webhook delivery {delivery_id} not found")
    except Exception as e:
        logger.error(f"Error retrying webhook delivery {delivery_id}: {str(e)}", exc_info=True)


@shared_task
def trigger_webhooks_for_event(event, payload):
    """
    Trigger all active webhooks for a specific event.
    """
    try:
        # Find all active webhooks subscribed to this event
        webhooks = Webhook.objects.filter(active=True, events__contains=[event])
        logger.info(f"Triggering {webhooks.count()} webhooks for event {event}")

        for webhook in webhooks:
            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event=event,
                payload=payload,
                status='pending'
            )

            # Queue delivery task
            process_webhook_delivery.delay(str(delivery.id))

    except Exception as e:
        logger.error(f"Error triggering webhooks for event {event}: {str(e)}", exc_info=True)


@shared_task
def clean_old_webhook_deliveries():
    """
    Clean up old webhook delivery records to manage database size.
    """
    try:
        # Keep successful deliveries for 30 days, failed ones for 90 days
        success_threshold = timezone.now() - timedelta(days=30)
        failure_threshold = timezone.now() - timedelta(days=90)

        # Delete old records
        old_success = WebhookDelivery.objects.filter(
            status='success',
            created_at__lt=success_threshold
        )
        success_count = old_success.count()
        old_success.delete()

        old_failure = WebhookDelivery.objects.filter(
            status='failed',
            created_at__lt=failure_threshold
        )
        failure_count = old_failure.count()
        old_failure.delete()

        logger.info(f"Cleaned {success_count} successful and {failure_count} failed webhook deliveries")

    except Exception as e:
        logger.error(f"Error cleaning webhook deliveries: {str(e)}", exc_info=True)