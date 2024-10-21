import logging

from django.core.management.base import BaseCommand

from publicatie_tabellen.pgdump_to_storage import PgDumpToStorage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options):
        try:
            app_names = ["publicatie_tabellen",]

            dump = PgDumpToStorage()
            dump.start_dump(app_names)
            dump.upload_to_blob()
            dump.remove_dump()
            
            logger.info("Completed DB dump")

        except Exception as e:
            logger.exception(
                f"An exception in dumping the publicationtables: {e}"
            )
