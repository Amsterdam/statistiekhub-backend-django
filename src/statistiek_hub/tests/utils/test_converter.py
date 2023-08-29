from django.test import TestCase
from statistiek_hub.utils import converter


class ConverterTestCase(TestCase):
    def test_float(self):
        """The index page loads properly"""
        response = converter.convert("12.2")
        self.assertEqual(response, 12.2)
