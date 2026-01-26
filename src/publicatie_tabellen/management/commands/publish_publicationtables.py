import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from opentelemetry import trace

from publicatie_tabellen.publication_main import PublishFunction

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populates publication tables"

    def handle(self, *args, **options) -> None:
        with tracer.start_as_current_span("publish") as span:
            self._handle(*args, **options)

    def _handle(self, *args, **options):
        try:
            with transaction.atomic():
                publ = PublishFunction()
                publ.run_all_publish_tables()

        except Exception as e:
            logger.exception(
                f"An exception in command publish_publicationtables observations: {e}"
            )
