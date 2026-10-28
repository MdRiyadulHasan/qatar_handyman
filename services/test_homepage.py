from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django_ckeditor_5.widgets import CKEditor5Widget
from .admin_forms import CategoryAdminForm, ServiceAdminForm
from .models import Category, HomeSlide, Service
from .templatetags.content_filters import richtext
from .test_images import image_file


class HomepageTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.media.cleanup)
        self.addCleanup(self.override.disable)
        self.category = Category.objects.create(name="Repairs", slug="repairs")
        self.service = Service.objects.create(category=self.category, name="Tap repair",
            slug="tap-repair", summary="Repair a tap", description="Plain description.")

    def test_homepage_order_all_categories_and_services(self):
        Category.objects.create(name="Empty category", slug="empty")
        hidden_category = Category.objects.create(name="Private category", slug="private", is_active=False)
        Service.objects.create(category=hidden_category, name="Private service", slug="private-service",
            summary="Private", description="Details")
        Service.objects.create(category=self.category, name="Hidden repair", slug="hidden-repair",
            summary="Hidden", description="Details", is_active=False)
        Service.objects.bulk_create([
            Service(category=self.category, name=f"Repair {i}", slug=f"repair-{i}",
                summary="Repair summary", description="Repair details") for i in range(8)
        ])
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Empty category")
        self.assertContains(response, "Repair 7")
        self.assertContains(response, self.service.get_absolute_url())
        self.assertNotContains(response, "Private category")
        self.assertNotContains(response, "Private service")
        self.assertNotContains(response, "Hidden repair")
        body = response.content.decode()
        self.assertLess(body.index('data-slider role='), body.index('id="categories-heading"'))
        self.assertLess(body.index('id="categories-heading"'), body.index('id="category-repairs"'))

    def test_admin_slides_supply_images_content_links_and_order(self):
        later = HomeSlide.objects.create(title="Later slide", subtitle="Separate slider content",
            image=image_file("later.png"), alt_text="Slider image", button_label="Browse repairs",
            button_url=self.category.get_absolute_url(), sort_order=2)
        first = HomeSlide.objects.create(title="First slide", image=image_file("first.png"), sort_order=1)
        HomeSlide.objects.create(title="Hidden slide", image=image_file("hidden.png"), is_active=False)
        HomeSlide.objects.create(title="Missing photo", image="")
        self.category.image = image_file("category.png")
        self.category.save()
        response = self.client.get(reverse("home"))
        slides = response.context["slides"]
        self.assertEqual([slide["title"] for slide in slides], [first.title, later.title])
        self.assertEqual(slides[0]["image_url"], first.image.url)
        self.assertEqual(slides[0]["alt_text"], first.title)
        self.assertEqual(slides[0]["button_url"], reverse("services:list"))
        self.assertEqual(slides[1]["image_url"], later.image.url)
        self.assertEqual(slides[1]["button_url"], self.category.get_absolute_url())
        self.assertEqual(slides[1]["subtitle"], later.subtitle)
        self.assertEqual(slides[1]["button_label"], later.button_label)
        self.assertEqual(slides[1]["alt_text"], later.alt_text)
        self.assertContains(response, "data-slider-prev")
        self.assertNotContains(response, "Hidden slide")
        self.assertNotContains(response, "Missing photo")

    def test_single_admin_slide_is_independent_of_categories(self):
        slide = HomeSlide.objects.create(title="Custom promotion", image=image_file("custom.png"))
        self.category.is_active = False
        self.category.save()
        response = self.client.get(reverse("home"))
        self.assertEqual([item["title"] for item in response.context["slides"]], [slide.title])
        self.assertNotContains(response, "data-slider-prev")

    def test_no_active_admin_slides_keeps_contact_fallback(self):
        HomeSlide.objects.create(title="Hidden slide", image=image_file("hidden.png"), is_active=False)
        response = self.client.get(reverse("home"))
        self.assertEqual(len(response.context["slides"]), 1)
        self.assertEqual(response.context["slides"][0]["button_url"], reverse("services:contact"))
        self.assertIn("home-illustration.svg", response.context["slides"][0]["image_url"])
        self.assertNotContains(response, "data-slider-prev")

    def test_slide_rejects_unsafe_links(self):
        slide = HomeSlide(title="Slide", image=image_file(), button_url="javascript:alert(1)")
        with self.assertRaises(ValidationError):
            slide.full_clean()

    def test_editor_widgets_and_form_media(self):
        for form_class in (CategoryAdminForm, ServiceAdminForm):
            form = form_class()
            self.assertIsInstance(form.fields["description"].widget, CKEditor5Widget)
            self.assertIn("django_ckeditor_5/dist/bundle.js", str(form.media))
            self.assertIn("django_ckeditor_5", str(form["description"]))

    def test_rich_text_formatting_is_sanitized_and_legacy_text_preserved(self):
        self.service.description = '<h2>Moving plan</h2><p><strong>Careful packing</strong></p><img src="/media/box.png" onerror="alert(1)"><a href="javascript:alert(1)">Unsafe</a><script>alert(1)</script>'
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "<h2>Moving plan</h2>")
        self.assertContains(response, "<strong>Careful packing</strong>")
        self.assertNotContains(response, "onerror=")
        self.assertNotContains(response, "javascript:")
        self.assertNotContains(response, "<script>alert")
        self.assertIn("<br>", richtext("First line\nSecond line"))

    def test_editor_image_upload_requires_staff_and_saves_in_media(self):
        url = reverse("ck_editor_5_upload_file")
        self.assertEqual(self.client.post(url, {"upload": image_file()}).status_code, 403)
        user = get_user_model().objects.create_user(username="editor", password="test-only", is_staff=True)
        self.client.force_login(user)
        response = self.client.post(url, {"upload": image_file()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["url"].startswith("/media/editor/"))
