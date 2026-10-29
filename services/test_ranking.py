from django.test import TestCase
from django.urls import reverse
from .admin_forms import CategoryAdminForm, ServiceAdminForm
from .models import Category, Service


class RankingTests(TestCase):
    def setUp(self):
        self.later_category = Category.objects.create(name="A repairs", slug="repairs", rank=20)
        self.first_category = Category.objects.create(name="Z moving", slug="moving", rank=10)
        self.later_service = Service.objects.create(
            category=self.first_category, name="A featured packing", slug="packing",
            summary="Packing", description="Details", rank=20, is_featured=True)
        self.first_service = Service.objects.create(
            category=self.first_category, name="Z furniture moving", slug="furniture",
            summary="Moving", description="Details", rank=10)
        self.repair = Service.objects.create(
            category=self.later_category, name="Tap repair", slug="tap",
            summary="Repair", description="Details", rank=0)

    def test_homepage_groups_services_under_ranked_category_headings(self):
        response = self.client.get(reverse("home"))
        categories = list(response.context["home_categories"])
        self.assertEqual(categories, [self.first_category, self.later_category])
        self.assertEqual(categories[0].home_services, [self.first_service, self.later_service])
        self.assertEqual(categories[1].home_services, [self.repair])
        body = response.content.decode().split('<div class="grouped-services">', 1)[1]
        positions = [
            body.index('id="heading-moving"'),
            body.index(self.first_service.get_absolute_url()),
            body.index(self.later_service.get_absolute_url()),
            body.index('id="heading-repairs"'),
            body.index(self.repair.get_absolute_url()),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_category_catalogue_uses_rank_before_featured_status(self):
        response = self.client.get(reverse("services:list"), {"category": self.first_category.slug})
        self.assertEqual(list(response.context["services"]), [self.first_service, self.later_service])
        # Equal ranks have a stable alphabetical fallback.
        self.later_service.rank = 10
        self.later_service.save()
        response = self.client.get(reverse("services:list"), {"category": self.first_category.slug})
        self.assertEqual(list(response.context["services"]), [self.later_service, self.first_service])

    def test_admin_forms_reject_negative_ranks(self):
        for form_class in (CategoryAdminForm, ServiceAdminForm):
            with self.subTest(form=form_class.__name__):
                form = form_class(data={"rank": -1})
                self.assertFalse(form.is_valid())
                self.assertIn("rank", form.errors)
