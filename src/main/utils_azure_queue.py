import logging
import os

from azure.identity import WorkloadIdentityCredential
from azure.storage.queue import QueueClient, QueueServiceClient
from django.conf import settings

log = logging.getLogger(__name__)


class AzureQueue:
    """singleton Queue"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureQueue, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _create_azure_queue_client():
        federated_token_file = os.getenv("AZURE_FEDERATED_TOKEN_FILE")
        if federated_token_file:
            credentials = WorkloadIdentityCredential()
            name_storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            queue_client = QueueClient(
                credential=credentials,
                account_url=f"https://{name_storage_account}.queue.core.windows.net",
                queue_name=settings.JOB_QUEUE_NAME,
            )

        elif hasattr(settings, "AZURITE_CONNECTION_STRING"):  # for local development
            queue_service_client = QueueServiceClient.from_connection_string(
                settings.AZURITE_CONNECTION_STRING
            )
            try:
                queue_service_client.create_queue(settings.JOB_QUEUE_NAME)
            except:  # for local development the error is not important
                pass
            queue_client = queue_service_client.get_queue_client(
                settings.JOB_QUEUE_NAME
            )

        else:
            raise Exception("cannot connect to queue")

        return queue_client

    @classmethod
    def get_queue_client(cls):
        if cls._client is None:
            cls._client = cls._create_azure_queue_client()
        return cls._client
