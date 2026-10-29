from decimal import Decimal
from io import StringIO
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from .models import Category, Service


class ServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Plumbing", slug="plumbing")
        cls.service = Service.objects.create(
            category=cls.category, name="Tap repair", slug="tap-repair",
            summary="Fix leaking taps", description="Inspect and repair taps.",
            starting_price=Decimal("75.00"),
        )

    def test_catalogue_detail_and_search(self):
        response = self.client.get(reverse("services:list"))
        self.assertContains(response, "Tap repair")
        self.assertContains(response, "QAR 75.00")
        self.assertContains(self.client.get(self.service.get_absolute_url()), "Inspect and repair taps.")
        self.assertContains(self.client.get(reverse("services:list"), {"q": "leaking"}), "Tap repair")
        search_response = self.client.get(reverse("services:list"), {"q": "painting"})
        self.assertEqual(list(search_response.context["services"]), [])
        main = search_response.content.decode().split('<main id="main">', 1)[1].split('</main>', 1)[0]
        self.assertNotIn("Tap repair", main)
        self.assertContains(self.client.get(reverse("services:list"), {"category": "plumbing"}), "Tap repair")
        missing_response = self.client.get(reverse("services:list"), {"category": "missing"})
        self.assertEqual(list(missing_response.context["services"]), [])

    def test_inactive_service_and_category_are_hidden(self):
        self.service.is_active = False
        self.service.save()
        self.assertNotContains(self.client.get(reverse("services:list")), "Tap repair")
        self.assertEqual(self.client.get(self.service.get_absolute_url()).status_code, 404)
        self.service.is_active = True
        self.service.save()
        self.category.is_active = False
        self.category.save()
        self.assertNotContains(self.client.get(reverse("services:list")), "Tap repair")
        self.assertEqual(self.client.get(self.service.get_absolute_url()).status_code, 404)

    def test_quote_only_and_zero_prices(self):
        self.service.starting_price = None
        self.service.save()
        self.assertContains(self.client.get(self.service.get_absolute_url()), "Price on request")
        self.service.starting_price = Decimal("0")
        self.service.save()
        self.assertContains(self.client.get(self.service.get_absolute_url()), "QAR 0.00")

    def test_negative_price_rejected(self):
        self.service.starting_price = Decimal("-1")
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_seed_command_is_repeatable_and_preserves_edits(self):
        call_command("seed_services", stdout=StringIO())
        count = Service.objects.count()
        service = Service.objects.get(slug="ac-servicing")
        service.summary = "Custom description"
        service.save()
        call_command("seed_services", stdout=StringIO())
        self.assertEqual(Service.objects.count(), count)
        service.refresh_from_db()
        self.assertEqual(service.summary, "Custom description")

    def test_pagination_keeps_filters(self):
        Service.objects.bulk_create([
            Service(category=self.category, name=f"Tap {i}", slug=f"tap-{i}",
                    summary="Tap maintenance", description="Repair")
            for i in range(13)
        ])
        response = self.client.get(reverse("services:list"), {"q": "Tap", "category": "plumbing"})
        self.assertContains(response, "q=Tap&amp;category=plumbing&amp;page=2")
        self.assertEqual(len(response.context["services"]), 12)
