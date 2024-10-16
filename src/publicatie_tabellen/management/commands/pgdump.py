import logging

from django.core.management.base import BaseCommand
from publicatie_tabellen.save_as_csv import SaveAsCsv

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options):
        try:
          dump = SaveAsCsv()
          app_names = ["publicatie_tabellen",]
          dump.main(app_names)  
        except Exception as e:
            logger.exception(
                f"An exception in dumping the publicationtables: {e}"
            )
