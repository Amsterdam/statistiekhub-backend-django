# Fix error: "connection already closed" 
# How to deal with long running processes initiated via manage.py command?
# see https://code.djangoproject.com/ticket/34914#comment:3 
# implemented solution from: https://forum.djangoproject.com/t/django-db-utils-interfaceerror-connection-already-closed-when-updating-from-django-3-0-to-3-1/12708/21

import django.db
from django.contrib.gis.db.backends.postgis.base import (
    DatabaseWrapper as BuiltinPostgresDatabaseWrapper,
)
from django.utils.asyncio import async_unsafe
from psycopg2 import InterfaceError


@async_unsafe
class DatabaseWrapper(BuiltinPostgresDatabaseWrapper):
    def create_cursor(self, name=None):
        try:
            return super().create_cursor(name=name)
        except InterfaceError:
            django.db.close_old_connections()
            django.db.connection.connect()
            return super().create_cursor(name=name)
