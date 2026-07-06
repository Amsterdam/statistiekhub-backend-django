import logging
import os
import shutil
import zipfile
from typing import Literal, TypeAlias

import django.apps
from django.core.files.storage import InvalidStorageError, default_storage, storages
from django.db import connection

from publicatie_tabellen.models import ChangesLog

logger = logging.getLogger(__name__)

ModelNameList: TypeAlias = list[str]
AppDumpSelection: TypeAlias = list[tuple[str, Literal["_all_"] | ModelNameList]]


class PgDumpToStorage:
    TMP_DIRECTORY = "/tmp/pgdump"

    def start_dump(self, app_names: AppDumpSelection) -> None:
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)
        for app, selection in app_names:
            models = self._resolve_models_to_dump(app, selection)
            for model in models:
                self._dump_model_to_csv_zip(model)

    def _resolve_models_to_dump(self, app: str, selection: Literal["_all_"] | ModelNameList):
        if selection == "_all_":
            return [model for model in django.apps.apps.get_app_config(app).get_models() if model != ChangesLog]

        if not isinstance(selection, list):
            raise TypeError(f"Expected a list of model names for app '{app}', got {type(selection).__name__}.")

        return [django.apps.apps.get_model(app, model_name) for model_name in selection]

    def _dump_model_to_csv_zip(self, model):
        table_name = model._meta.db_table
        filepath = os.path.join(self.TMP_DIRECTORY, f"{table_name}.csv.zip")
        csv_filename = "data.csv"
        select_query = f"SELECT * FROM {table_name}"

        # Open the ZIP file for writing
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Open a writable stream inside the ZIP file for the CSV
            with zip_file.open(csv_filename, "w") as csv_file:
                # stream data directly into the ZIP
                sql = f"COPY ({select_query}) TO STDOUT WITH CSV HEADER"
                with connection.cursor() as cursor:
                    cursor.copy_expert(sql, csv_file)

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
    """Set storage to pgdump container
    and overwrite existing files instead of using hash postfixes."""

    def __init__(self, *args, **kwargs):
        try:
            self.storage = storages["pgdump"]
        except InvalidStorageError:
            self.storage = default_storage

    def __getattr__(self, name):
        return getattr(self.storage, name)

    def save_without_postfix(self, name, content):
        if self.exists(name):
            self.delete(name)
        return self.save(name, content)

    def get_available_name(self, name, max_length=None):
        return name
