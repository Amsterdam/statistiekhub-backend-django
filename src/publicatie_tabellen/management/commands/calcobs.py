import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from publicatie_tabellen.publication_main import PublishFunction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dump publication-tables to storagecontainer pgdump"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # calculate observations
                publ = PublishFunction()
                publ.fill_observationcalculated()

        except Exception as e:
            logger.exception(
                f"An exception in command calculate observations: {e}"
            )
