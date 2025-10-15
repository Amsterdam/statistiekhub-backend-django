import json

import pytest
from model_bakery import baker

from import_export_job.models import ImportJob
from job_consumer.job_tools import store_job_in_queue
from job_consumer.queue_job_consumer import AzureJobQueueConsumer
from main.utils_azure_queue import AzureQueue


class TestJobConsumer:

    queue_client = AzureQueue.get_queue_client()

    @staticmethod
    def queue_message_count(queue_client) -> int:
        properties = queue_client.get_queue_properties()
        count = properties.approximate_message_count
        return count

    def test_store_job_in_queue(self):

        self.queue_client.clear_messages()
        assert self.queue_message_count(self.queue_client) == 0

        store_job_in_queue(job_pk=1, dry_run=False)
        assert self.queue_message_count(self.queue_client) == 1

        message_iterator = self.queue_client.receive_messages(max_messages=1)
        for message in message_iterator:
            job = json.loads(message.content)
            assert job["key"] == 1
            assert job["dry_run"] == False

    @pytest.mark.django_db(transaction=True)
    def test_AzureJobQueueConsumer(self):

        self.queue_client.clear_messages()
        assert self.queue_message_count(self.queue_client) == 0
        job = baker.make(ImportJob)
        # Test job in queue
        assert self.queue_message_count(self.queue_client) == 1

        consumer = AzureJobQueueConsumer(end_at_empty_queue=True)
        consumer.run()

        # Test whether the records that were in the queue are correctly removed
        assert self.queue_message_count(self.queue_client) == 0
