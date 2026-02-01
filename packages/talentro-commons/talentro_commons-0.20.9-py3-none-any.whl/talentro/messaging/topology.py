import aio_pika

from typing import List, Tuple, Optional

FIVE_MINUTES = 5 * 60 * 1000
FIFTEEN_MINUTES = 15 * 60 * 1000

class TopologyConfig:
    def __init__(
        self,
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType,
        bindings: List[Tuple[str, str]],
        dlx_name: str = None,
        retry_config: Optional[dict] = None
    ):
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.bindings = bindings
        self.dlx_name = dlx_name
        self.retry_config = retry_config

    def get_max_retries(self, queue_name: str) -> int:
        """Get max retries for a specific queue, default 3."""
        if not self.retry_config:
            return 3
        return self.retry_config.get(queue_name, {}).get("max_retries", 3)


FRONTEND_TOPOLOGY = TopologyConfig(
    exchange_name="x.frontend",
    exchange_type=aio_pika.ExchangeType.TOPIC,
    bindings=[
        ("q.frontend.updates.gateway", "frontend.update"),
    ],
    retry_config={
        "q.frontend.updates.gateway": {"enabled": False}
    }
)


APPLICATIONS_TOPOLOGY = TopologyConfig(
    exchange_name="x.applications",
    exchange_type=aio_pika.ExchangeType.TOPIC,
    bindings=[
        # Integrations
        ("q.applications.raw.integrations", "applications.raw"),
        ("q.applications.send.integrations", "applications.send"),

        # Acquisitions
        ("q.applications.saved.acquisitions", "applications.saved"),

        # Vacancies
        ("q.applications.saved.vacancies", "applications.saved"),

        # Candidates
        ("q.applications.normalized.candidates", "applications.normalized"),
        ("q.applications.external.upserted.candidates", "applications.external.upserted"),
    ],
    dlx_name="x.applications.dlx",
    retry_config={
        # Integrations
        "q.applications.raw.integrations": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3},
        "q.applications.send.integrations": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3},

        # Acquisitions
        "q.applications.saved.acquisitions": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3},

        # Vacancies
        "q.applications.saved.vacancies": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3},

        # Candidates
        "q.applications.normalized.candidates": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3},
        "q.applications.external.upserted.candidates": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3}
    }
)


FEEDS_TOPOLOGY = TopologyConfig(
    exchange_name="x.feeds",
    exchange_type=aio_pika.ExchangeType.TOPIC,
    bindings=[
        # Acquisitions
        ("q.feeds.sync.acquisitions", "feeds.sync"),
    ],
    dlx_name="x.feeds.dlx",
    retry_config={
        "q.feeds.sync.acquisitions": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3}
    }
)

BILLING_TOPOLOGY = TopologyConfig(
    exchange_name="x.billing",
    exchange_type=aio_pika.ExchangeType.TOPIC,
    bindings=[
        # Billing
        ("q.billing.events.billing", "billing.event"),
    ],
    dlx_name="x.billing.dlx",
    retry_config={
        "q.billing.events.billing": {"enabled": True, "ttl_ms": FIVE_MINUTES, "max_retries": 3}
    }
)