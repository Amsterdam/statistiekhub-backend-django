import pytest
from django.conf import settings
from django.core.files.storage import storages


@pytest.fixture(scope="session", autouse=True)
def init_azurite_storage_containers() -> None:
    """
    Ensure Azurite storage containers exist when running tests.
    Only runs if Azurite is configured.
    """

    if not getattr(settings, "AZURITE_CONNECTION_STRING", None):
        return

    from django.core.files.storage import default_storage

    if hasattr(default_storage, "client"):
        if not default_storage.client.exists():
            default_storage.client.create_container()

    if not getattr(settings, "STORAGES", None):
        return

    for storage in settings.STORAGES:
        if (
            hasattr(storages[storage], "client")
            and not storages[storage].client.exists()
        ):
            storages[storage].client.create_container()
