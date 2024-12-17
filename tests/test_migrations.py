from django.core.management import call_command
from django.test import TestCase


class MigrationTestCase(TestCase):
    def test_missing_migrations(self):
        """
        Test and assert that all models are fully covered by migrations.
        Any missing migrations will fail this test.
        """
        call_command("makemigrations", "--check", "--no-input", "--dry-run")
