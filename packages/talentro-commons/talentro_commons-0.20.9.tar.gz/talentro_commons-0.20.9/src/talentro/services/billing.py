from datetime import datetime, UTC
from functools import wraps
from http import HTTPStatus

from ..constants import ErrorCode, DisplayMessage, SKU
from ..event import Message, Event, EventMeta
from ..exceptions import APIException
from ..services.rabbitmq import QueueContext


def billable_event(sku: SKU, details=None):

    if details is None:
        details = {}

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not kwargs.get("x_organization_id"):
                raise APIException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    message="No organization provided",
                    error_code=ErrorCode.BAD_REQUEST,
                    display_message=DisplayMessage.BAD_REQUEST,
                )

            result = func(*args, **kwargs)

            organization_id = kwargs.get("x_organization_id")

            await send_billing_event(sku, organization_id, 1, details)
            return result

        return wrapper

    return decorator


async def send_billing_event(sku: SKU, organization_id: str, count: int = 1, details=None):
    if details is None:
        details = {}

    # Send message to billing queue
    context: QueueContext = QueueContext()

    metadata = EventMeta(
        event_type='billing.event',
        source="commons",
        idempotency_key=f"sku:{sku}:count:{count}:org:{str(organization_id)}:unix:{datetime.now(UTC).timestamp()}",
    )

    event = Event(
        payload={
            "sku": sku,
            "count": count,
            "organization_id": organization_id,
            "details": details
        },
        meta=metadata,
        organization_id=str(organization_id)
    )

    message = Message(
        event=event,
        exchange="x.billing",
        routing_key="billing.event",
    )

    await context.send_message(message)
    print(f"[Billing] Billed event with sku: '{sku}' x {count} usages to org: {organization_id}.")
