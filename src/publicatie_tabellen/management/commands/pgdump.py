import logging

from django.db import transaction
from django.core.management.base import BaseCommand

from publicatie_tabellen.publication_main import PublishFunction
from publicatie_tabellen.models import PublicationUpdatedAt
from publicatie_tabellen.pgdump_to_storage import PgDumpToStorage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # calculate all publication-tables
                updated_at = PublicationUpdatedAt.objects.last()
                PublishFunction.run_all_publish_tables()
                updated_at.save()
            
                # pg_dump tables
                app_names = ["publicatie_tabellen",]

                dump = PgDumpToStorage()
                try:                    
                    dump.start_dump(app_names)
                    dump.upload_to_blob()
                    dump.remove_dump()
                    
                    logger.info("Completed DB dump")
                except Exception as e:
                    logger.exception(f"An exception occurred during pg_dump: {e}")
                    raise  # transaction rollback

        except Exception as e:
            logger.exception(
                f"An exception in dumping the publicationtables: {e}"
            )
            raise
