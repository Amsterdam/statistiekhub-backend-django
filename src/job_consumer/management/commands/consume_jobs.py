import logging

from django.core.management.base import BaseCommand
from opentelemetry import trace

from job_consumer.queue_job_consumer import AzureJobQueueConsumer

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start job consumer to process job requests"

    def handle(self, *args, **options) -> None:
        with tracer.start_as_current_span("consume_jobs") as span:
            self._handle(*args, **options)

    def _handle(self, *args, **options):
        logger.info("Job Consumer started")

        try:
            consumer = AzureJobQueueConsumer()
            consumer.run()
        except Exception as e:
            logger.exception(e)
