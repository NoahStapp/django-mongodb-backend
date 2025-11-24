from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.db import NotSupportedError
from django.test import TestCase, skipUnlessDBFeature

from .models import City, Zipcode


@skipUnlessDBFeature("gis_enabled")
class LookupTests(TestCase):
    fixtures = ["initial"]

    def test_unsupported(self):
        msg = "MongoDB does not support the 'same_as' lookup."
        with self.assertRaisesMessage(NotSupportedError, msg):
            City.objects.get(point__same_as=Point(95, 30))

    def test_contains(self):
        houston = City.objects.get(name="Houston")
        qs = City.objects.filter(point__contains=Point(-95.363151, 29.763374))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(houston, qs.first())

    def test_disjoint(self):
        houston = City.objects.get(name="Houston")
        qs = City.objects.filter(point__disjoint=Point(100, 50))
        self.assertIn(houston, qs)

    def test_distance_gt(self):
        houston = City.objects.get(name="Houston")
        dallas = City.objects.get(name="Dallas")  # Roughly ~363 km from Houston
        qs = City.objects.filter(point__distance_gt=(houston.point, 362826))
        self.assertEqual(qs.count(), 6)
        self.assertNotIn(dallas, list(qs))

    def test_distance_gte(self):
        houston = City.objects.get(name="Houston")
        dallas = City.objects.get(name="Dallas")  # Roughly ~363 km from Houston
        qs = City.objects.filter(point__distance_gte=(houston.point, 362825))
        self.assertEqual(qs.count(), 7)
        self.assertIn(dallas, list(qs))

    def test_distance_lt(self):
        houston = City.objects.get(name="Houston")
        qs = City.objects.filter(point__distance_lt=(houston.point, 362825))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(houston, qs.first())

    def test_distance_lte(self):
        houston = City.objects.get(name="Houston")
        dallas = City.objects.get(name="Dallas")  # Roughly ~363 km from Houston
        qs = City.objects.filter(point__distance_lte=(houston.point, 362826))
        self.assertEqual(qs.count(), 2)
        self.assertEqual([houston, dallas], list(qs))

    def test_distance_units(self):
        chicago = City.objects.get(name="Chicago")
        lawrence = City.objects.get(name="Lawrence")
        qs = City.objects.filter(point__distance_lt=(chicago.point, Distance(km=720)))
        self.assertEqual(qs.count(), 2)
        self.assertEqual([lawrence, chicago], list(qs))
        qs = City.objects.filter(point__distance_lt=(chicago.point, Distance(mi=447)))
        self.assertEqual(qs.count(), 2)
        self.assertEqual([lawrence, chicago], list(qs))

    def test_dwithin(self):
        houston = City.objects.get(name="Houston")
        qs = City.objects.filter(point__dwithin=(houston.point, 0.2))
        self.assertEqual(qs.count(), 5)

    def test_dwithin_unsupported_units(self):
        qs = City.objects.filter(point__dwithin=(Point(40.7670, -73.9820), Distance(km=1)))
        with self.assertRaisesMessage(
            ValueError,
            "Only numeric values of radian units are allowed on geodetic distance queries.",
        ):
            qs.first()

    def test_intersects(self):
        city = City.objects.create(point=Point(95, 30))
        qs = City.objects.filter(point__intersects=Point(95, 30).buffer(10))
        self.assertEqual(qs.count(), 1)
        self.assertIn(city, qs)

    def test_within(self):
        zipcode = Zipcode.objects.get(code="77002")
        qs = City.objects.filter(point__within=zipcode.poly).values_list("name", flat=True)
        self.assertEqual(["Houston"], list(qs))
