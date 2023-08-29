from django.test import TestCase
from statistiek_hub.models import Unit


class UnitTestCase(TestCase):
    def setUp(self):
        Unit.objects.create(name="aantal", code=None, symbol=None)
        Unit.objects.create(name="percentage", code="_P", symbol="%")

    def test_get_objects(self):
        aantal = Unit.objects.get(name="aantal")
        percentage = Unit.objects.get(name="percentage")

        self.assertEqual(str(aantal), "aantal")
        self.assertEqual(str(percentage), "percentage")
