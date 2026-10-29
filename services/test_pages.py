import json
import re
from datetime import timedelta
from io import StringIO
from xml.etree.ElementTree import fromstring
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Category, Inquiry, Service


class PremiumPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_services", stdout=StringIO())

    def test_new_pages_render_unique_metadata_and_navigation(self):
        paths = [reverse("home")] + [
            reverse(f"services:{name}") for name in ("list", "moving", "about", "areas", "faq", "contact")
        ]
        titles = []
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<link rel="canonical"')
            self.assertContains(response, '<meta name="description"')
            self.assertContains(response, 'Moving &amp; shifting')
            self.assertContains(response, 'QATAR MOVE &amp; FIX')
            self.assertContains(response, 'Qatar Move &amp; Fix')
            self.assertNotContains(response, 'Qatar Handyman')
            titles.append(response.context["seo_title"])
        self.assertEqual(len(titles), len(set(titles)))

    @override_settings(SITE_URL="https://handyman.example")
    def test_sitemap_uses_configured_domain_and_excludes_inactive_content(self):
        service = Service.objects.get(slug="office-relocation")
        service.is_active = False
        service.save()
        Category.objects.filter(slug="plumbing").update(is_active=False)
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        xml = fromstring(response.content)
        urls = [node.text for node in xml.findall("{*}url/{*}loc")]
        self.assertIn("https://handyman.example/services/moving-shifting/", urls)
        self.assertNotIn("https://handyman.example/services/office-relocation/", urls)
        self.assertNotIn("https://handyman.example/services/plumbing-repairs/", urls)
        self.assertNotContains(response, "/admin/")
        robots = self.client.get(reverse("robots"))
        self.assertContains(robots, "Sitemap: https://handyman.example/sitemap.xml")

    def test_search_is_noindex_and_pagination_has_its_own_canonical(self):
        response = self.client.get(reverse("services:list"), {"q": "move"})
        self.assertContains(response, 'content="noindex,follow"')
        category = Category.objects.get(slug="moving-shifting")
        Service.objects.bulk_create([
            Service(category=category, name=f"Extra {i}", slug=f"extra-{i}",
                    summary="Extra service", description="Description")
            for i in range(13)
        ])
        response = self.client.get(reverse("services:list"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["canonical_url"].endswith("?page=2"))
        self.assertIn("Page 2", response.context["seo_title"])

    def test_moving_catalogue_has_four_services(self):
        self.assertEqual(Service.objects.filter(category__slug="moving-shifting").count(), 4)
        response = self.client.get(reverse("services:moving"))
        self.assertContains(response, "House &amp; apartment shifting")
        self.assertContains(response, "Office relocation")
        self.assertContains(response, "Packing &amp; unpacking")

    def payload(self):
        return {"name": "Test Customer", "email": "customer@example.com",
                "phone": "+974 1234 5678", "area": "Doha",
                "preferred_date": (timezone.localdate() + timedelta(days=2)).isoformat(),
                "message": "Please quote for packing and moving my apartment."}

    def test_quote_request_saved_and_service_preselected(self):
        service = Service.objects.get(slug="house-apartment-shifting")
        url = reverse("services:contact")
        response = self.client.get(url, {"service": service.slug})
        self.assertEqual(response.context["form"].initial["service"], service.pk)
        payload = self.payload()
        payload["service"] = service.pk
        response = self.client.post(url, payload, follow=True)
        self.assertContains(response, "Your request has been received")
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.service, service)
        self.assertEqual(inquiry.status, Inquiry.Status.NEW)
        self.client.get(url)
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_invalid_date_phone_and_hidden_service_rejected(self):
        payload = self.payload()
        payload["preferred_date"] = (timezone.localdate() - timedelta(days=1)).isoformat()
        payload["phone"] = "--------"
        service = Service.objects.get(slug="office-relocation")
        service.is_active = False
        service.save()
        payload["service"] = service.pk
        response = self.client.post(reverse("services:contact"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertIn("phone", response.context["form"].errors)
        self.assertIn("preferred_date", response.context["form"].errors)
        self.assertIn("service", response.context["form"].errors)

    def test_form_enforces_csrf_and_admin_requires_login(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("services:contact"), self.payload()).status_code, 403)
        self.assertEqual(self.client.get("/admin/services/inquiry/").status_code, 302)

    def test_structured_data_escapes_admin_content_and_uses_editable_metadata(self):
        service = Service.objects.get(slug="office-relocation")
        service.summary = "</script><script>alert(1)</script>"
        service.meta_title = "Custom moving title"
        service.meta_description = "Custom moving description"
        service.save()
        response = self.client.get(service.get_absolute_url())
        self.assertEqual(response.context["seo_title"], "Custom moving title")
        self.assertEqual(response.context["seo_description"], "Custom moving description")
        source = re.search(r'<script type="application/ld\+json">(.*?)</script>',
                           response.content.decode(), flags=re.S).group(1)
        self.assertNotIn("</script>", source)
        data = json.loads(source)
        self.assertEqual(data["@graph"][0]["description"], service.summary)

    def test_service_slug_cannot_shadow_content_pages(self):
        service = Service.objects.first()
        service.slug = "contact"
        with self.assertRaises(ValidationError):
            service.full_clean()
