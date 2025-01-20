import logging
import os
import shutil

import django.apps
from django.conf import settings
from django.db import connection
from django.utils.module_loading import import_string as get_storage_class

from publicatie_tabellen.utils import convert_queryset_into_dataframe

logger = logging.getLogger(__name__)


class PgDumpToStorage:
    TMP_DIRECTORY = "/tmp/pgdump"

    def start_dump(self, app_names:list):
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)
        for app in app_names:
            for model in django.apps.apps.get_app_config(app).get_models():
                self._dump_model_to_csv_zip(model)

    def _dump_model_to_csv_zip(self, model):
        table_name = model._meta.db_table
        filepath = os.path.join(
            self.TMP_DIRECTORY, f"{table_name}.csv.zip"
        )  # filename is model name

        qs = model.objects.all()
        df = convert_queryset_into_dataframe(qs)
        df.to_csv(filepath, compression="zip", index=False, sep=';')
        logger.info(f"Successfully dumped {filepath}")

        return filepath

    def upload_to_blob(self):
        storage = OverwriteStorage()
        for file in os.listdir(self.TMP_DIRECTORY):
            filepath = os.path.join(self.TMP_DIRECTORY, file)
            with open(filepath, "rb") as f:
                storage.save_without_postfix(name=os.path.join("pgdump", file), content=f)
            logger.info(f"Successfully uploaded {filepath} to blob")

    def remove_dump(self):
        """
        Removes the files locally when processing is done
        """
        shutil.rmtree(self.TMP_DIRECTORY)


class OverwriteStorage:
    """ Set storage to pgdump container
        and overwrite existing files instead of using hash postfixes."""

    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'STORAGE_AZURE'):
            # Gebruik de 'pgdump' opslagconfiguratie
            storage_class = get_storage_class(settings.STORAGES['pgdump']['BACKEND'])
            storage_options = settings.STORAGES['pgdump']['OPTIONS']
        else:
            # Gebruik de standaard opslagconfiguratie
            storage_class = get_storage_class(settings.STORAGES['default']['BACKEND'])
            storage_options = {}
        
        self.storage = storage_class(**storage_options)


    def __getattr__(self, name):
        return getattr(self.storage, name)
    
    def save_without_postfix(self, name, content):
        if self.exists(name):
            self.delete(name)
        return self.save(name, content)

    def get_available_name(self, name, max_length=None):
        return name
