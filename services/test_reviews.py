from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from .models import CustomerReview


class CustomerReviewTests(TestCase):
    def review(self, **kwargs):
        values = {"customer_name": "Test Customer", "rating": 4, "review": "Feedback for testing."}
        values.update(kwargs)
        return CustomerReview.objects.create(**values)

    def test_empty_section_and_unpublished_reviews(self):
        draft = self.review(review="Unpublished feedback")
        self.assertFalse(draft.is_published)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Happy customers. Real experiences.")
        self.assertContains(response, "Your experience matters.")
        self.assertNotContains(response, draft.review)

    def test_published_reviews_order_stars_and_optional_details(self):
        self.review(customer_name="Later Customer", sort_order=10, is_published=True)
        self.review(customer_name="First Customer", sort_order=1, location="Lusail",
                    service_name="Carpet installation", rating=3, is_published=True)
        response = self.client.get(reverse("home"))
        self.assertEqual([review.customer_name for review in response.context["customer_reviews"]],
                         ["First Customer", "Later Customer"])
        self.assertContains(response, "Lusail")
        self.assertContains(response, "Carpet installation")
        self.assertContains(response, 'aria-label="Rated 3 out of 5 stars"')
        self.assertNotContains(response, "Your experience matters.")

    def test_review_content_is_escaped(self):
        self.review(customer_name="<b>Customer</b>", review='<script>alert("test")</script>', is_published=True)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, '<script>alert("test")</script>')
        self.assertContains(response, "&lt;script&gt;")
        self.assertContains(response, "&lt;b&gt;Customer&lt;/b&gt;")

    def test_invalid_rating_rejected_by_validation_and_database(self):
        for rating in (0, 6):
            with self.subTest(rating=rating):
                review = CustomerReview(customer_name="Test", rating=rating, review="Test feedback")
                with self.assertRaises(ValidationError):
                    review.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    review.save()

    def test_unpublishing_and_deleting_remove_review(self):
        review = self.review(review="Distinctive published feedback", is_published=True)
        self.assertContains(self.client.get(reverse("home")), review.review)
        review.is_published = False
        review.save()
        self.assertNotContains(self.client.get(reverse("home")), review.review)
        review.delete()
        self.assertContains(self.client.get(reverse("home")), "Your experience matters.")

    def test_admin_can_create_and_publish_reviews(self):
        url = reverse("admin:services_customerreview_add")
        self.assertEqual(self.client.get(url).status_code, 302)
        user = get_user_model().objects.create_superuser("reviewadmin", "reviewadmin@example.com", "test-password")
        self.client.force_login(user)
        response = self.client.post(url, {"customer_name": "Admin Test Customer", "rating": 5,
                                         "review": "Admin-managed feedback", "sort_order": 0,
                                         "is_published": "on", "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        review = CustomerReview.objects.get()
        self.assertTrue(review.is_published)
        self.assertContains(self.client.get(reverse("home")), review.review)
