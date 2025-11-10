from .celery import app as celery_app
from .kombu.transport.azure_storage_queue import register_transport

register_transport()

__all__ = ("celery_app",)
