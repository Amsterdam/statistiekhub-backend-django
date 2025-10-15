from main.utils_azure_queue import AzureQueue


def test_singleton_queue():
    # Singleton test
    queueclient_1 = AzureQueue()
    queueclient_2 = AzureQueue()
    assert queueclient_1 is queueclient_2
    assert queueclient_1.get_queue_client() is queueclient_2.get_queue_client()
