import json

from main.utils_azure_queue import AzureQueue

JOB_MESSAGE_VERSION_NAME = "Statistiek_job_v1"

def store_job_in_queue(job_pk, dry_run):
    import_job = json.dumps(
        {
            "version": JOB_MESSAGE_VERSION_NAME,
            "key": job_pk,
            "dry_run": dry_run
        }
    )

    queue_client = AzureQueue.get_queue_client()
    queue_client.send_message(import_job)

