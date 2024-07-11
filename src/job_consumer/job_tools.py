import json

from job_consumer.utils_azure_que import get_queue_client

JOB_MESSAGE_VERSION_NAME = "Statistiek_job_v1"

def store_job_in_queue(job_pk, dry_run):
    import_job = json.dumps(
        {
            "version": JOB_MESSAGE_VERSION_NAME,
            "key": job_pk,
            "dry_run": dry_run
        }
    )

    queue_client = get_queue_client()
    queue_client.send_message(import_job)

