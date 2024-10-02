import logging

from azure.core.exceptions import ResourceExistsError
from azure.identity import WorkloadIdentityCredential
from azure.storage.queue import QueueClient, QueueServiceClient
from django.conf import settings

log = logging.getLogger(__name__)


def get_queue_client():
    return settings.QUEUE_CLIENT