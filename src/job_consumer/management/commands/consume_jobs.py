import logging

from django.core.management.base import BaseCommand

from job_consumer.queue_job_consumer import AzureJobQueueConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start job consumer to process job requests"

    def handle(self, *args, **options):
        logger.info("Job Consumer started")

        try:
            consumer = AzureJobQueueConsumer()
            consumer.run()
        except Exception as e:
            logger.exception(e)
