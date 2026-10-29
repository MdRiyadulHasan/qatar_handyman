from io import BytesIO
from tempfile import TemporaryDirectory
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from .models import Category, CategoryImage, Service, ServiceImage


def image_file(name="photo.png"):
    output = BytesIO()
    Image.new("RGB", (12, 8), "blue").save(output, "PNG")
    return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")


class ImageTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.media.cleanup)
        self.addCleanup(self.override.disable)
        self.category = Category.objects.create(name="Moving", slug="moving")
        self.service = Service.objects.create(category=self.category, name="House moving",
            slug="house-moving", summary="Move your home", description="Moving details.")

    def test_main_images_upload_and_category_fallback(self):
        self.category.image = image_file("category.png")
        self.category.image_alt = "Packed boxes"
        self.category.save()
        response = self.client.get(reverse("services:list"))
        self.assertContains(response, self.category.image.url)
        self.service.image = image_file("service.png")
        self.service.image_alt = "Furniture being moved"
        self.service.save()
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, self.service.image.url)
        self.assertContains(response, 'alt="Furniture being moved"')
        self.assertTrue(self.service.image.storage.exists(self.service.image.name))

    def test_service_gallery_order_visibility_and_multiple_images(self):
        ServiceImage.objects.create(service=self.service, image=image_file("second.png"),
            caption="Second photo", sort_order=2)
        ServiceImage.objects.create(service=self.service, image=image_file("first.png"),
            caption="First photo", sort_order=1)
        hidden = ServiceImage.objects.create(service=self.service, image=image_file("hidden.png"),
            caption="Unpublished photo", is_active=False)
        response = self.client.get(self.service.get_absolute_url())
        self.assertContains(response, "First photo")
        self.assertContains(response, "Second photo")
        self.assertNotContains(response, hidden.image.url)
        body = response.content.decode()
        self.assertLess(body.index("First photo"), body.index("Second photo"))

    def test_category_gallery_rendered_when_category_selected(self):
        photo = CategoryImage.objects.create(category=self.category, image=image_file(),
            caption="Category photograph", alt_text="Boxes in a room")
        response = self.client.get(reverse("services:list"), {"category": self.category.slug})
        self.assertContains(response, photo.image.url)
        self.assertContains(response, "Category photograph")
        self.assertContains(response, 'alt="Boxes in a room"')
        self.category.is_active = False
        self.category.save()
        self.assertNotContains(self.client.get(reverse("services:list"),
            {"category": self.category.slug}), photo.image.url)

    def test_upload_validation_rejects_fake_image_and_oversized_file(self):
        class UploadForm(forms.ModelForm):
            class Meta:
                model = ServiceImage
                fields = ("image",)
        form = UploadForm(files={"image": SimpleUploadedFile("fake.png", b"not an image")})
        self.assertFalse(form.is_valid())
        photo = ServiceImage(service=self.service, image=image_file())
        photo.image.file.size = 10 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            photo.full_clean()

    def test_images_optional_for_existing_records(self):
        self.assertEqual(self.client.get(self.service.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("services:list")).status_code, 200)

    def test_upload_paths_separate_categories_and_services(self):
        self.category.image = image_file("category-main.png")
        self.category.save()
        self.service.image = image_file("service-main.png")
        self.service.save()
        category_photo = CategoryImage.objects.create(category=self.category, image=image_file("category-gallery.png"))
        service_photo = ServiceImage.objects.create(service=self.service, image=image_file("service-gallery.png"))
        for field, expected in (
            (self.category.image, "categories/covers/"),
            (self.service.image, "services/covers/"),
            (category_photo.image, "categories/gallery/"),
            (service_photo.image, "services/gallery/"),
        ):
            self.assertTrue(field.name.startswith(expected))
            self.assertTrue(field.url.startswith("/media/" + expected))
            self.assertTrue(field.storage.exists(field.name))

    def test_uploaded_media_can_be_served_from_media_root(self):
        from types import ModuleType
        from django.urls import re_path
        from django.views.static import serve
        photo = ServiceImage.objects.create(service=self.service, image=image_file())
        media_urls = ModuleType("test_media_urls")
        media_urls.urlpatterns = [
            re_path(r"^media/(?P<path>.*)$", serve, {"document_root": self.media.name}),
        ]
        with override_settings(ROOT_URLCONF=media_urls):
            response = self.client.get(photo.image.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertTrue(b"".join(response.streaming_content).startswith(b"\x89PNG"))

    def test_service_cards_use_gallery_photos_in_category_lists(self):
        hidden = ServiceImage.objects.create(service=self.service, image=image_file("hidden-cover.png"),
            is_active=False, sort_order=0)
        photo = ServiceImage.objects.create(service=self.service, image=image_file("gallery-cover.png"),
            alt_text="Moving service photo", sort_order=1)
        for path, params in ((reverse("home"), {}), (reverse("services:list"), {"category": self.category.slug})):
            response = self.client.get(path, params)
            self.assertContains(response, photo.image.url)
            self.assertContains(response, 'alt="Moving service photo"')
            self.assertNotContains(response, hidden.image.url)
        photo.is_active = False
        photo.save()
        category_photo = CategoryImage.objects.create(category=self.category,
            image=image_file("category-fallback.png"), alt_text="Category fallback")
        response = self.client.get(reverse("services:list"), {"category": self.category.slug})
        self.assertContains(response, category_photo.image.url)

    def test_category_lists_show_main_image_or_first_active_gallery_image(self):
        hidden = CategoryImage.objects.create(category=self.category,
            image=image_file("hidden-category.png"), sort_order=0, is_active=False)
        later = CategoryImage.objects.create(category=self.category,
            image=image_file("later-category.png"), sort_order=20)
        first = CategoryImage.objects.create(category=self.category,
            image=image_file("first-category.png"), sort_order=10, alt_text="Category boxes")
        for path in (reverse("home"), reverse("services:list")):
            body = self.client.get(path).content.decode()
            grid = body.split('<div class="grid service-grid category-card-grid">', 1)[1].split("</section>", 1)[0]
            self.assertIn(first.image.url, grid)
            self.assertIn('alt="Category boxes"', grid)
            self.assertNotIn(hidden.image.url, grid)
            self.assertNotIn(later.image.url, grid)
        self.category.image = image_file("main-category.png")
        self.category.image_alt = "Category main photo"
        self.category.save()
        body = self.client.get(reverse("home")).content.decode()
        grid = body.split('<div class="grid service-grid category-card-grid">', 1)[1].split("</section>", 1)[0]
        self.assertIn(self.category.image.url, grid)
        self.assertIn('alt="Category main photo"', grid)
        self.assertNotIn(first.image.url, grid)
