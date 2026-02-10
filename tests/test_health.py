import pytest
from django.test.utils import override_settings

from health.views import health


class TestHealth:
    @pytest.mark.django_db
    def test_health_db(self, client):
        """# check database"""
        response = health(client)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    def test_health_debug_true(self, client):
        "debug = true"
        response = health(client)
        assert response.status_code == 500
