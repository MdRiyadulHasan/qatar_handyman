import json
import re
from django.test import RequestFactory, TestCase, override_settings
from .models import Category, Service
from .seo import absolute_url, breadcrumb_schema


@override_settings(SITE_URL="https://qatarmoveandfix.com")
class SearchReadinessTests(TestCase):
    def test_absolute_urls_do_not_duplicate_origin(self):
        request = RequestFactory().get("/")
        self.assertEqual(absolute_url(request, "/services/"), "https://qatarmoveandfix.com/services/")
        self.assertEqual(absolute_url(request, "https://qatarmoveandfix.com/services/"), "https://qatarmoveandfix.com/services/")
        self.assertEqual(absolute_url(request, "https://other.example/image.jpg"), "https://other.example/image.jpg")
        schema = breadcrumb_schema(request, [("Services", "https://qatarmoveandfix.com/services/")])
        self.assertEqual(schema["itemListElement"][0]["item"], "https://qatarmoveandfix.com/services/")

    def test_homepage_has_one_descriptive_h1_and_business_graph(self):
        response = self.client.get("/")
        html = response.content.decode()
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
        self.assertContains(response, "<h1>Your move. Your repairs. One local team.</h1>", html=True)
        self.assertNotContains(response, 'id="home-services-heading"')
        graph = json.loads(response.context["schema_json"])["@graph"]
        organization = next(item for item in graph if item["@type"] == "Organization")
        self.assertEqual(organization["url"], "https://qatarmoveandfix.com/")
        self.assertEqual(organization["telephone"], "+97466433172")
        self.assertIn("/static/services/", organization["logo"])
        self.assertNotIn("aggregateRating", organization)
        self.assertContains(response, 'property="og:image"')

    @override_settings(GOOGLE_SITE_VERIFICATION="test-verification-token")
    def test_optional_google_verification(self):
        self.assertContains(self.client.get("/"), '<meta name="google-site-verification" content="test-verification-token">')

    @override_settings(GOOGLE_SITE_VERIFICATION="")
    def test_missing_verification_is_omitted(self):
        self.assertNotContains(self.client.get("/"), 'name="google-site-verification"')

    def test_service_canonical_and_structured_breadcrumb_are_valid(self):
        category = Category.objects.create(name="Repairs", slug="repairs")
        service = Service.objects.create(category=category, name="Tap Repair", slug="tap-repair", summary="Tap repairs", description="Scope")
        response = self.client.get(service.get_absolute_url())
        graph = json.loads(response.context["schema_json"])["@graph"]
        expected = "https://qatarmoveandfix.com/services/tap-repair/"
        self.assertEqual(response.context["canonical_url"], expected)
        self.assertEqual(graph[1]["itemListElement"][-1]["item"], expected)

    def test_robots_and_sitemap_expose_the_production_domain(self):
        self.assertContains(self.client.get("/robots.txt"), "Sitemap: https://qatarmoveandfix.com/sitemap.xml")
        self.assertContains(self.client.get("/sitemap.xml"), "https://qatarmoveandfix.com/")

    def test_moving_landing_includes_current_moving_category(self):
        category = Category.objects.create(name="Moving & Shifting", slug="moving-shifting-services-qatar")
        service = Service.objects.create(category=category, name="Furniture Transport", slug="furniture-transport", summary="Transport items", description="Scope")
        response = self.client.get("/services/moving-shifting/")
        self.assertContains(response, service.name)
        self.assertEqual(response.context["seo_title"], "House & Office Moving in Qatar | Qatar Move & Fix")
