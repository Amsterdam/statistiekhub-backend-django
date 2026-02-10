import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from opentelemetry import trace

from publicatie_tabellen.models import ChangesLog, PublicationUpdatedAt
from publicatie_tabellen.pgdump_to_storage import PgDumpToStorage
from publicatie_tabellen.publication_main import PublishFunction

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options) -> None:
        with tracer.start_as_current_span("pgdump") as span:  # noqa: F841
            self._handle(*args, **options)

    def _handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info("start publicationtables command")
                # calculate all publication-tables
                updated = PublicationUpdatedAt.objects.order_by("-updated_at").first()
                if not updated:
                    updated = PublicationUpdatedAt(updated_at=datetime.datetime(1900, 10, 1))

                # only run if something changed
                latest_change = ChangesLog.objects.order_by("-changed_at").first()
                if latest_change.changed_at <= updated.updated_at:
                    logger.info("No changes in tables")
                    return

                PublishFunction.run_all_publish_tables()
                updated.save()
                changed = True

        except Exception as e:
            logger.exception(f"An exception in calculating all publicationtables: {e}")
            return

        if changed:
            try:
                # pg_dump tables
                app_names = [
                    "publicatie_tabellen",
                ]
                dump = PgDumpToStorage()

                dump.start_dump(app_names)
                dump.upload_to_blob()
                dump.remove_dump()

                logger.info("Completed DB dump")

            except Exception as e:
                logger.exception(f"An exception occurred during pg_dump: {e}")
