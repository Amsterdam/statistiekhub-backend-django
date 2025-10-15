from main.utils_azure_queue import AzureQueue
from main.utils_azure_storage import AzureStorage


def test_singleton_queue():
    # Singleton test
    queueclient_1 = AzureQueue()
    queueclient_2 = AzureQueue()
    assert queueclient_1 is queueclient_2
    assert queueclient_1.get_queue_client() is queueclient_2.get_queue_client()


def test_singleton_blobserviceclient():
    # Singleton test
    blobserviceclient_1 = AzureStorage()
    blobserviceclient_2 = AzureStorage()
    assert blobserviceclient_1 is blobserviceclient_2
    assert (
        blobserviceclient_1.get_blob_service_client()
        is blobserviceclient_2.get_blob_service_client()
    )
