import pytest
from asgiref.sync import sync_to_async
from django.db import connection
from psycopg2 import InterfaceError


@pytest.mark.django_db
def test_create_cursor_success():
    with connection.cursor() as cursor:
        assert cursor is not None


@pytest.mark.django_db(transaction=True)
def test_create_cursor_interface_error():
    connection.close()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)
    except InterfaceError:
        pytest.fail("InterfaceError: De verbinding kon niet opnieuw worden geopend.")


@pytest.mark.django_db(transaction=True)
def test_async_unsafe_decorator():
    async def async_test():
        connection.close()
        try:
            await sync_to_async(connection.cursor)()
        except RuntimeError as e:
            assert str(e) == "You cannot call this from an async context - use a thread or sync_to_async."
