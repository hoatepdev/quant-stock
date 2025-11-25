"""Celery application configuration for background task processing."""

from celery import Celery

from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "vietnam_quant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.core.tasks.data_ingestion",
        "src.core.tasks.factor_calculation",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    # Task routing
    task_routes={
        "src.core.tasks.data_ingestion.*": {"queue": "data_ingestion"},
        "src.core.tasks.factor_calculation.*": {"queue": "factor_calculation"},
    },
    # Task time limits
    task_soft_time_limit=600,  # 10 minutes
    task_time_limit=900,  # 15 minutes
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

logger.info("Celery application configured successfully")
