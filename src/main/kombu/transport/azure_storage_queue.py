import json
import logging
import os
from queue import Empty
from urllib.parse import unquote_plus

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueServiceClient, TextBase64EncodePolicy
from kombu.transport import virtual

logger = logging.getLogger()


class Channel(virtual.Channel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        conninfo = self.connection.client
        hostname = conninfo.hostname or "127.0.0.1"
        port = conninfo.port
        userid = conninfo.userid or "devstoreaccount1"
        password = unquote_plus(conninfo.password) if conninfo.password else None

        # Determine authentication method
        if userid.lower() == "workloadidentitycredential":
            # Use Workload Identity (federated token)
            self._init_workload_identity()
        elif hostname.lower() in ("127.0.0.1", "localhost", "azurite") or userid.lower() == "devstoreaccount1":
            # Azurite connection
            self._init_azurite(hostname, port, userid, password)
        else:
            # Connection not (yet) implemented
            raise NotImplementedError(f"Authentication method not implemented for {userid}")

        self._queue_cache = {}

    def _init_workload_identity(self):
        from azure.identity import WorkloadIdentityCredential

        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        logger.info(f"Initializing Azure Queue with Workload Identity for account: {storage_account}")

        credentials = WorkloadIdentityCredential()
        account_url = f"https://{storage_account}.queue.core.windows.net"

        self.queue_service = QueueServiceClient(
            account_url=account_url,
            credential=credentials,
            message_encode_policy=TextBase64EncodePolicy(),
        )

    def _init_azurite(self, hostname, port, userid, password):
        connection_string = (
            f"DefaultEndpointsProtocol=http;"
            f"AccountName={userid};"
            f"AccountKey={password};"
            f"QueueEndpoint=http://{hostname}:{port}/{userid};"
        )

        logger.info(f"Initializing Azurite connection at {hostname}:{port}")

        self.queue_service = QueueServiceClient.from_connection_string(
            connection_string, message_encode_policy=TextBase64EncodePolicy()
        )

    def _get_queue(self, queue_name):
        if queue_name not in self._queue_cache:
            # Azure Storage Queue names must be lowercase and alphanumeric
            safe_name = queue_name.lower().replace("_", "-").replace(".", "-")
            queue_client = self.queue_service.get_queue_client(safe_name)

            try:
                queue_client.create_queue()
            except ResourceExistsError:
                pass

            self._queue_cache[queue_name] = queue_client

        return self._queue_cache[queue_name]

    def _put(self, queue, message, **kwargs):
        queue_client = self._get_queue(queue)
        msg_body = json.dumps(message)
        queue_client.send_message(msg_body)

    def _get(self, queue, timeout=None):
        queue_client = self._get_queue(queue)

        visibility_timeout = timeout if timeout else 30
        messages = queue_client.receive_messages(messages_per_page=1, visibility_timeout=visibility_timeout)

        try:
            message = next(messages)
        except StopIteration:
            raise Empty()

        payload = json.loads(message.content)
        queue_client.delete_message(message.id, message.pop_receipt)

        return payload

    def _delete(self, queue, *args, **kwargs):
        """
        Messages are auto-deleted in _get() because Azure doesn't support traditional message acknowledgment patterns.
        This method is kept for compatibility but is a no-op.
        """
        return

    def _size(self, queue):
        try:
            return self._get_queue(queue).get_queue_properties().approximate_message_count
        except Exception:
            return 0

    def _purge(self, queue):
        queue_client = self._get_queue(queue)

        try:
            queue_client.clear_messages()
        except Exception:
            pass

        return 0

    def close(self):
        super().close()
        self._queue_cache.clear()


class Transport(virtual.Transport):
    Channel = Channel

    default_port = 10001
    driver_type = "azurestoragequeue"
    driver_name = "azurestoragequeue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def driver_version(self):
        try:
            import azure.storage.queue

            return azure.storage.queue.__version__
        except Exception:
            return "unknown"


def register_transport():
    from kombu.transport import TRANSPORT_ALIASES

    TRANSPORT_ALIASES["azurestoragequeue"] = __name__ + ":Transport"
