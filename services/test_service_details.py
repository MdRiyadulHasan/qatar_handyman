import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from django.core.management import call_command
from django.test import TestCase
from django.utils.html import escape
from .models import Category, Service


class ServiceDetailPresentationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Moving", slug="moving")
        self.service = Service.objects.create(category=self.category, name="House Shifting",
            slug="house-shifting", summary="Plan a home move", description="Original description")

    def test_refresh_preview_does_not_modify_content(self):
        output = StringIO()
        call_command("update_service_details", stdout=output)
        self.service.refresh_from_db()
        self.assertEqual(self.service.description, "Original description")
        self.assertIn("Preview: 1 services", output.getvalue())

    def test_refresh_backs_up_copy_and_preserves_url_price_and_custom_fields(self):
        self.service.meta_title = "Prior title"
        self.service.starting_price = 250
        self.service.service_area = "Doha, Lusail"
        self.service.faqs = [{"question": "Custom question?", "answer": "Custom answer."}]
        self.service.save()
        with TemporaryDirectory() as directory:
            call_command("update_service_details", apply=True, backup_dir=directory, stdout=StringIO())
            files = list(Path(directory).glob("*.json"))
            self.assertEqual(len(files), 1)
            backup = json.loads(files[0].read_text(encoding="utf-8"))[0]
            self.assertEqual(backup["description"], "Original description")
            self.assertEqual(backup["meta_title"], "Prior title")
        self.service.refresh_from_db()
        self.assertEqual(self.service.slug, "house-shifting")
        self.assertEqual(self.service.starting_price, 250)
        self.assertEqual(self.service.service_area, "Doha, Lusail")
        self.assertEqual(self.service.faqs[0]["question"], "Custom question?")
        self.assertIn("<ul><li>", self.service.description)
        self.assertIn("Doha, Qatar", self.service.seo_heading)
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, escape(self.service.seo_heading))
        self.assertContains(response, "What you can request")
        self.assertContains(response, '<li>Doha</li>', html=True)
        self.assertContains(response, "Custom question?")

    def test_refresh_adds_locations_and_faqs_only_when_blank(self):
        with TemporaryDirectory() as directory:
            call_command("update_service_details", apply=True, backup_dir=directory, stdout=StringIO())
        self.service.refresh_from_db()
        self.assertIn("The Pearl-Qatar", self.service.service_area)
        self.assertEqual(len(self.service.faqs), 2)
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "The Pearl-Qatar")
        self.assertContains(response, "building permissions")
        self.assertNotContains(response, "Same-day availability")

    def test_title_does_not_repeat_qatar_and_admin_heading_takes_priority(self):
        self.service.name = "House Shifting in Qatar"
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertEqual(response.context["seo_title"], "House Shifting in Qatar | Qatar Move & Fix")
        self.assertEqual(response.context["service_heading"], "House Shifting in Qatar")
        self.service.seo_heading = "An administrator-written service heading"
        self.service.save()
        self.assertContains(self.client.get(self.service.get_absolute_url()), '<h1>An administrator-written service heading</h1>', html=True)

    def test_category_areas_inherit_and_escape_html(self):
        self.category.service_area = "Doha, <script>bad</script>, Lusail"
        self.category.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertEqual(response.context["service_locations"], ["Doha", "<script>bad</script>", "Lusail"])
        self.assertContains(response, "&lt;script&gt;bad&lt;/script&gt;")
        self.assertNotContains(response, "<script>bad</script>")

    def test_enquiry_area_fallback_does_not_invent_schema_coverage(self):
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "The Pearl-Qatar")
        data = json.loads(response.context["schema_json"])
        self.assertEqual(data["@graph"][0]["areaServed"], {"@type": "Country", "name": "Qatar"})
