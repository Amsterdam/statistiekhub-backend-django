import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from opentelemetry import trace

from publicatie_tabellen.publication_main import PublishFunction

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populates tabel observationcalculated"

    def handle(self, *args, **options) -> None:
        with tracer.start_as_current_span("calcobs") as span:
            self._handle(*args, **options)

    def _handle(self, *args, **options):
        try:
            with transaction.atomic():
                # calculate observations
                publ = PublishFunction()
                publ.fill_observationcalculated()

        except Exception as e:
            logger.exception(f"An exception in command calculate observations: {e}")
