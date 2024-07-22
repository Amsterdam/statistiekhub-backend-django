import json
import logging
import time

import timeout_decorator

from import_export_job.tasks import run_import_job
from job_consumer import job_tools
from job_consumer.utils_azure_que import get_queue_client

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


class AzureJobQueueConsumer:
    # Be careful with the visibility timeout! If the message is still processing when the visibility timeout
    # expires, the message will be put back on the queue and will be processed again. This can lead to duplicate
    # messages!!! Always use a timeout decorator to prevent this.
    # We set it to an hour, because some zips can simply be very very large
    MESSAGE_VISIBILITY_TIMEOUT = 3600

    # This consumer accepts messages with this name
    MESSAGE_VERSION_NAME = job_tools.JOB_MESSAGE_VERSION_NAME

    def __init__(self, end_at_empty_queue=False):
        self.queue_client = get_queue_client()
        self.end_at_empty_queue = end_at_empty_queue

    def get_queue_length(self):
        properties = self.queue_client.get_queue_properties()
        count = properties.approximate_message_count
        return count

    def run(self):
        while True:
            count = self.get_queue_length()
            message_iterator = None

            if self.end_at_empty_queue:
                # This part is only for testing purposes. To be able to exit the running process when the queue is empty.
                message_iterator = [
                    m
                    for m in self.queue_client.receive_messages(
                        messages_per_page=10, visibility_timeout=5
                    )
                ]
                if count == 0 or len(message_iterator) == 0:
                    break

            if count == 0:
                time.sleep(5)
                continue

            if message_iterator is None:
                message_iterator = self.queue_client.receive_messages(
                    max_messages=1, visibility_timeout=self.MESSAGE_VISIBILITY_TIMEOUT
                )

            for message in message_iterator:
                self.process_message(message)
                self.queue_client.delete_message(message.id, message.pop_receipt)

    @timeout_decorator.timeout(MESSAGE_VISIBILITY_TIMEOUT)
    def process_message(self, message):

        logger.info("Started process_message")

        job = json.loads(message.content)
        if not job["version"] == self.MESSAGE_VERSION_NAME:
            return

        # Run task
        try: 
            run_import_job(job["key"], job["dry_run"])
        except:
            raise Exception("Failed ")
