import logging

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from django.conf import settings

log = logging.getLogger(__name__)


class AzureStorage:
    ''' singleton Storage BlobServiceClient'''
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureStorage, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _create_azure_blob_service_client() -> BlobServiceClient:
        if hasattr(settings, 'STORAGE_AZURE'):
            account_name = settings.STORAGE_AZURE["default"]["OPTIONS"]["account_name"]
            credential = DefaultAzureCredential()

            blob_service_client = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=credential
            )

            return blob_service_client

    @classmethod
    def get_blob_service_client(cls):
        if cls._client is None:
            cls._client = cls._create_azure_blob_service_client
        return cls._client
        