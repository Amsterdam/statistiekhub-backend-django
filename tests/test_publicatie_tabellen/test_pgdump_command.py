import os
import shutil
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.storage import Storage
from django.core.management import call_command

from publicatie_tabellen.management.commands.pgdump import Command
from publicatie_tabellen.save_as_csv import SaveAsCsv
from referentie_tabellen.models import Theme


class TestSaveAsCsv:
    @patch("publicatie_tabellen.save_as_csv.SaveAsCsv._dump_model_to_csv")
    def test_start_dump(self, mock_dump):
        SaveAsCsv().start_dump(["publicatie_tabellen",])
        assert os.path.isdir(SaveAsCsv.TMP_DIRECTORY)
        assert mock_dump.called

        shutil.rmtree(SaveAsCsv.TMP_DIRECTORY)

    @pytest.mark.django_db
    def test_dump_model_csv(self):
        os.makedirs(SaveAsCsv.TMP_DIRECTORY, exist_ok=True)
        filepath = SaveAsCsv()._dump_model_to_csv(Theme)

        count = Theme.objects.all().count()

        assert os.path.isfile(filepath)
        # check if file contains header and all rows
        with open(filepath, "r") as f:
            assert len(f.readlines()) == 1 + count
        os.remove(filepath)

    def test_upload_to_blob(self):
        os.makedirs(SaveAsCsv.TMP_DIRECTORY, exist_ok=True)
        file_name = "test.csv"
        open(os.path.join(SaveAsCsv.TMP_DIRECTORY, file_name), "w").close()
        assert os.path.isfile(os.path.join(SaveAsCsv.TMP_DIRECTORY, file_name))

        SaveAsCsv().upload_to_blob()
        stored_file = os.path.join(settings.MEDIA_ROOT, "pgdump", file_name)
        assert os.path.isfile(stored_file)
        os.remove(stored_file)

class TestPgdumpCommand:
    @pytest.mark.django_db
    def test_pg_dump(self):
        """
        Check the whole happy flow
        """
        call_command("pgdump")

        assert not os.path.isdir(SaveAsCsv.TMP_DIRECTORY)
        assert len(os.listdir(os.path.join(settings.MEDIA_ROOT, "pgdump"))) > 1
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, "pgdump"))  # post cleanup