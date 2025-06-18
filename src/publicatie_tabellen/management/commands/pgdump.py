import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from publicatie_tabellen.models import ChangesLog, PublicationUpdatedAt
from publicatie_tabellen.pgdump_to_storage import PgDumpToStorage
from publicatie_tabellen.publication_main import PublishFunction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # calculate all publication-tables
                updated = PublicationUpdatedAt.objects.order_by('-updated_at').first()
                if not updated:
                    updated = PublicationUpdatedAt(updated_at=datetime.datetime(1900,10,1))

                # only run if something changed
                latest_change = ChangesLog.objects.order_by('-changed_at').first()
                if latest_change.changed_at <= updated.updated_at:
                    logger.info("No changes in tables")
                    changed = False
                    return  # Stop de transactie
                
                PublishFunction.run_all_publish_tables()
                updated.save()
                changed = True

        except Exception as e:
            changed = False
            logger.exception(
                f"An exception in calculating all publicationtables: {e}"
            )

        if changed:  
            try:               
                # pg_dump tables
                app_names = ["publicatie_tabellen",]
                dump = PgDumpToStorage()
                    
                dump.start_dump(app_names)
                dump.upload_to_blob()
                dump.remove_dump()
                
                logger.info("Completed DB dump")

            except Exception as e:
                logger.exception(
                    f"An exception occurred during pg_dump: {e}"
                )
