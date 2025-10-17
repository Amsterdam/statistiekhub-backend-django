import shutil
import tempfile

import pytest
from django.conf import settings


# because problem with writepermission when no azurestorage
@pytest.fixture(scope="session", autouse=True)
def temporary_media_root():
    """Fixture for temp media dir"""
    temp_media = tempfile.mkdtemp(prefix="test_media_")
    settings.MEDIA_ROOT = temp_media
    yield
    shutil.rmtree(temp_media)
