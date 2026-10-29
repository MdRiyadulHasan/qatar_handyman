from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator, RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from .validators import validate_image_size, validate_seo_faqs


class SEOFields(models.Model):
    seo_heading = models.CharField(max_length=200, blank=True, help_text="Optional page H1; defaults to the name.")
    focus_keyword = models.CharField(max_length=200, blank=True, help_text="Editorial planning only; not output as a keywords meta tag.")
    canonical_url = models.URLField(max_length=500, blank=True, validators=[URLValidator(schemes=["http", "https"])], help_text="Optional absolute HTTP(S) canonical URL. Leave blank for this page's URL.")
    robots_index = models.BooleanField(default=True, help_text="Allow search engines to index this page.")
    robots_follow = models.BooleanField(default=True, help_text="Allow crawlers to follow links on this page.")
    robots_max_snippet = models.IntegerField(default=-1, validators=[MinValueValidator(-1)], help_text="-1: no snippet limit; 0: no text snippet; positive number: character limit.")
    robots_max_image_preview = models.CharField(max_length=8, default="large", choices=[("none", "None"), ("standard", "Standard"), ("large", "Large")])
    include_in_sitemap = models.BooleanField(default=True, help_text="Only active, indexable pages with their own canonical URL are included.")
    breadcrumb_title = models.CharField(max_length=100, blank=True, help_text="Short breadcrumb label; defaults to the name.")
    og_title = models.CharField(max_length=200, blank=True, help_text="Social sharing title; defaults to the SEO title.")
    og_description = models.CharField(max_length=500, blank=True, help_text="Social sharing description; defaults to the meta description.")
    social_image = models.ImageField(upload_to="seo/social/%Y/%m/", max_length=255, blank=True, validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size], help_text="Social preview image; a landscape image around 1200 x 630 works well. Falls back to the cover/gallery image.")
    social_image_alt = models.CharField(max_length=300, blank=True, help_text="Describe the social preview image for accessibility.")
    twitter_title = models.CharField(max_length=200, blank=True, help_text="X/Twitter title; defaults to the Open Graph title.")
    twitter_description = models.CharField(max_length=500, blank=True, help_text="X/Twitter description; defaults to the Open Graph description.")
    twitter_card = models.CharField(max_length=20, default="summary_large_image", choices=[("summary", "Summary"), ("summary_large_image", "Large image")])
    service_area = models.CharField(max_length=500, blank=True, help_text="Actual service areas, separated by commas. Leave blank for Qatar.")
    faqs = models.JSONField(default=list, blank=True, validators=[validate_seo_faqs], help_text='Optional visible FAQs: [{"question": "Your question?", "answer": "Your answer."}]. Use plain text.')

    class Meta:
        abstract = True


class Category(SEOFields):
    name = models.CharField(max_length=100, unique=True)
    rank = models.PositiveIntegerField(default=0, db_index=True, help_text="Lower numbers appear first.")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="categories/covers/%Y/%m/", max_length=255, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
        help_text="Optional main image, up to 10 MB. Add extra photos in the gallery below.",
    )
    image_alt = models.CharField(max_length=200, blank=True, help_text="Describe the image for accessibility.")
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("services:category", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["rank", "name", "pk"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name



    @property
    def card_photo(self):
        if self.image:
            return {"url": self.image.url, "alt": self.image_alt or self.name}
        photos = getattr(self, "active_gallery_images", None)
        photo = photos[0] if photos else None
        if photos is None:
            photo = self.images.filter(is_active=True).first()
        if photo:
            return {"url": photo.image.url, "alt": photo.alt_text or photo.caption or self.name}
        from django.templatetags.static import static
        return {"url": static("services/home-illustration.svg"), "alt": self.name}

class Service(SEOFields):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=150)
    rank = models.PositiveIntegerField(default=0, db_index=True, help_text="Lower numbers appear first within the category.")
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=250)
    description = models.TextField()
    image = models.ImageField(
        upload_to="services/covers/%Y/%m/", max_length=255, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
        help_text="Optional main image, up to 10 MB. Add extra photos in the gallery below.",
    )
    image_alt = models.CharField(max_length=200, blank=True, help_text="Describe the image for accessibility.")
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    starting_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Starting price in QAR. Leave blank for quote-only services.",
    )
    schema_service_type = models.CharField(max_length=150, blank=True, help_text="Structured-data service type; defaults to the category name.")
    estimated_duration = models.CharField(max_length=100, blank=True, help_text="For example: 1–2 hours")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "name", "pk"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(starting_price__gte=0) | models.Q(starting_price__isnull=True),
                name="service_price_nonnegative",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.slug in {"moving-shifting", "about", "areas", "faq", "contact"}:
            raise ValidationError({"slug": "This slug is reserved for a website page."})


    @property
    def card_photo(self):
        if self.image:
            return {"url": self.image.url, "alt": self.image_alt or self.name}
        candidates = (
            (self, "Service photo"),
            (self.category, "Category photo"),
        )
        for owner, fallback_alt in candidates:
            if owner is self.category and owner.image:
                return {"url": owner.image.url, "alt": owner.image_alt or owner.name}
            photos = getattr(owner, "active_gallery_images", None)
            photo = photos[0] if photos else None
            if photos is None:
                photo = owner.images.filter(is_active=True).first()
            if photo:
                return {"url": photo.image.url, "alt": photo.alt_text or photo.caption or owner.name}
        from django.templatetags.static import static
        return {"url": static("services/home-illustration.svg"),
                "alt": "Illustration of furniture and moving boxes"}

    def get_absolute_url(self):
        return reverse("services:detail", kwargs={"slug": self.slug})


class Inquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWED = "reviewed", "Reviewed"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, validators=[
        RegexValidator(
            regex=r"^\+?[0-9 ()-]{8,30}$", message="Enter a phone number with 8–30 characters (digits, spaces, +, brackets or hyphens)."
        )
    ])
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="inquiries")
    area = models.CharField(max_length=250)
    preferred_date = models.DateField(null=True, blank=True)
    message = models.TextField(max_length=5000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

    def __str__(self):
        return f"{self.name} - {self.service or 'General enquiry'}"


class GalleryImage(models.Model):
    image = models.ImageField(
        upload_to="gallery/%Y/%m/", max_length=255,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=250, blank=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "pk"]

    def __str__(self):
        return self.caption or self.image.name


class CategoryImage(GalleryImage):
    image = models.ImageField(
        upload_to="categories/gallery/%Y/%m/", max_length=255,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="images")

    class Meta(GalleryImage.Meta):
        abstract = False
        verbose_name = "category gallery image"


class ServiceImage(GalleryImage):
    image = models.ImageField(
        upload_to="services/gallery/%Y/%m/", max_length=255,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")

    class Meta(GalleryImage.Meta):
        abstract = False
        verbose_name = "service gallery image"

class HomeSlide(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(
        upload_to="homepage/slides/%Y/%m/", max_length=255,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )
    alt_text = models.CharField(max_length=200, blank=True)
    button_label = models.CharField(max_length=50, default="Explore services")
    button_url = models.CharField(max_length=250, blank=True, help_text="Local path such as /services/ or a full HTTPS URL.")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "pk"]
        verbose_name = "homepage slide"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.button_url:
            from urllib.parse import urlsplit
            from django.core.validators import URLValidator
            target = urlsplit(self.button_url)
            if target.scheme or target.netloc:
                URLValidator(schemes=["https", "http"])(self.button_url)
            elif not self.button_url.startswith("/") or self.button_url.startswith("//") or "\\" in self.button_url:
                raise ValidationError({"button_url": "Enter a local path starting with / or a full HTTP(S) URL."})


class CustomerReview(models.Model):
    customer_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, help_text="Optional city or area, such as Doha or Lusail.")
    service_name = models.CharField(max_length=150, blank=True, help_text="Optional service the customer received.")
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} / 5") for i in range(1, 6)], validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(max_length=2000, help_text="The customer's actual feedback. Use plain text.")
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first on the homepage.")
    is_published = models.BooleanField(default=False, help_text="Publish only genuine feedback you have permission to display.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at", "-pk"]
        constraints = [models.CheckConstraint(check=models.Q(rating__gte=1, rating__lte=5), name="customer_review_rating_range")]

    def __str__(self):
        return f"{self.customer_name} ({self.rating}/5)"
