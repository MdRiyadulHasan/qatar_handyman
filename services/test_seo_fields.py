import json
import re
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Category, Service


@override_settings(SITE_URL="https://handyman.example")
class SEOFieldTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repairs", slug="repairs", description="Home repairs")
        self.service = Service.objects.create(category=self.category, name="Tap repair", slug="tap-repair",
                                              summary="Repair your tap", description="Service information")

    def graph(self, response):
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)
        return json.loads(match.group(1))["@graph"]

    def test_category_metadata_heading_and_canonical_are_used(self):
        self.category.meta_title = "Repairs in Doha"
        self.category.meta_description = "Book home repairs in Doha."
        self.category.seo_heading = "Home repairs in Qatar"
        self.category.breadcrumb_title = "Repairs team"
        self.category.save()
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Home repairs in Qatar</h1>', html=True)
        self.assertEqual(response.context["seo_title"], "Repairs in Doha")
        self.assertEqual(response.context["seo_description"], self.category.meta_description)
        self.assertEqual(response.context["canonical_url"], "https://handyman.example/services/category/repairs/")
        self.assertTrue(response.context["robots"].startswith("index,follow"))
        self.assertEqual(self.graph(response)[0]["@type"], "CollectionPage")
        legacy = self.client.get(reverse("services:list"), {"category": "repairs"})
        self.assertEqual(legacy.context["canonical_url"], response.context["canonical_url"])

    def test_social_overrides_and_fallbacks(self):
        self.service.og_title = "Share this repair"
        self.service.og_description = "Help with your tap"
        self.service.twitter_title = "Tap help on X"
        self.service.social_image = "seo/social/repair.jpg"
        self.service.social_image_alt = "A repaired tap"
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, 'property="og:title" content="Share this repair"')
        self.assertContains(response, 'name="twitter:title" content="Tap help on X"')
        self.assertContains(response, 'property="og:image" content="https://handyman.example/media/seo/social/repair.jpg"')
        self.assertContains(response, 'name="twitter:image:alt" content="A repaired tap"')
        self.assertContains(response, 'name="twitter:card" content="summary_large_image"')

    def test_noindex_nofollow_and_sitemap_exclusion(self):
        self.service.robots_index = False
        self.service.robots_follow = False
        self.service.robots_max_snippet = 0
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertEqual(response.context["robots"], "noindex,nofollow,max-snippet:0,max-image-preview:large")
        sitemap = self.client.get(reverse("sitemap"))
        self.assertNotContains(sitemap, "https://handyman.example" + self.service.get_absolute_url())
        self.assertContains(sitemap, "https://handyman.example" + self.category.get_absolute_url())
        self.category.include_in_sitemap = False
        self.category.save()
        self.assertNotContains(self.client.get(reverse("sitemap")), self.category.get_absolute_url())

    def test_custom_canonical_is_used_and_not_duplicated_in_sitemap(self):
        self.service.canonical_url = "https://other.example/repairs/"
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertEqual(response.context["canonical_url"], self.service.canonical_url)
        self.assertEqual(self.graph(response)[0]["url"], self.service.canonical_url)
        self.assertNotContains(self.client.get(reverse("sitemap")), self.service.get_absolute_url())

    def test_category_pagination_and_search_rules(self):
        Service.objects.bulk_create([Service(category=self.category, name=f"Extra {i}", slug=f"extra-{i}",
            summary="Repair", description="Repair") for i in range(13)])
        response = self.client.get(self.category.get_absolute_url(), {"page": 2})
        self.assertTrue(response.context["canonical_url"].endswith("/repairs/?page=2"))
        self.assertIn("Page 2", response.context["seo_title"])
        self.assertEqual(self.graph(response)[0]["mainEntity"]["itemListElement"][0]["position"], 13)
        response = self.client.get(self.category.get_absolute_url(), {"q": "repair"})
        self.assertTrue(response.context["robots"].startswith("noindex,follow"))

    def test_structured_faqs_are_visible_and_safe(self):
        self.service.faqs = [{"question": "Can you repair my tap?", "answer": "Yes. </script><script>alert(1)</script>"}]
        self.service.service_area = "Doha, Lusail"
        self.service.schema_service_type = "Tap maintenance"
        self.service.starting_price = 75
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "Can you repair my tap?")
        self.assertNotContains(response, "</script><script>alert(1)</script>")
        graph = self.graph(response)
        self.assertEqual(graph[-1]["@type"], "FAQPage")
        self.assertEqual(graph[0]["serviceType"], "Tap maintenance")
        self.assertEqual(graph[0]["areaServed"][0]["name"], "Doha")
        self.assertEqual(graph[0]["offers"]["priceSpecification"]["priceCurrency"], "QAR")
        self.category.faqs = [{"question": "Where?", "answer": "In Doha."}]
        self.category.save()
        response = self.client.get(self.category.get_absolute_url())
        self.assertContains(response, "In Doha.")
        self.assertEqual(self.graph(response)[-1]["@type"], "FAQPage")

    def test_invalid_metadata_is_rejected(self):
        for invalid in [{"question": "Wrong shape"}, [{"question": "Missing answer"}], [{"question": " ", "answer": "Hi"}]]:
            self.service.faqs = invalid
            with self.assertRaises(ValidationError):
                self.service.full_clean()
        self.service.faqs = []
        self.service.canonical_url = "ftp://example.com/page"
        with self.assertRaises(ValidationError):
            self.service.full_clean()
        self.service.canonical_url = ""
        self.service.robots_max_snippet = -2
        with self.assertRaises(ValidationError):
            self.service.full_clean()

    def test_inactive_and_unknown_categories_return_404(self):
        self.category.is_active = False
        self.category.save()
        self.assertEqual(self.client.get(self.category.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(reverse("services:category", kwargs={"slug": "missing"})).status_code, 404)
