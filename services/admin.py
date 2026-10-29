from .admin_forms import CategoryAdminForm, ServiceAdminForm
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Category, CategoryImage, CustomerReview, HomeSlide, Inquiry, Service, ServiceImage


admin.site.site_header = "Qatar Move & Fix administration"
admin.site.site_title = "Qatar Move & Fix"
admin.site.index_title = "Manage services and enquiries"


SEO_FIELDSETS = (
    ("Search engine content", {"fields": ("meta_title", "meta_description", "seo_heading", "focus_keyword", "breadcrumb_title")}),
    ("Indexing and canonical URL", {"classes": ("collapse",), "fields": ("canonical_url", "robots_index", "robots_follow", "robots_max_snippet", "robots_max_image_preview", "include_in_sitemap")}),
    ("Social sharing previews", {"classes": ("collapse",), "fields": ("og_title", "og_description", "social_image", "social_image_alt", "twitter_title", "twitter_description", "twitter_card")}),
    ("Local service information and FAQs", {"classes": ("collapse",), "fields": ("service_area", "faqs")}),
)


class GalleryInline(admin.TabularInline):
    fields = ("image", "preview", "alt_text", "caption", "sort_order", "is_active")
    readonly_fields = ("preview",)
    extra = 1

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" alt="" style="width:100px;height:70px;object-fit:cover">', obj.image.url)
        return "No image"


class CategoryImageInline(GalleryInline):
    model = CategoryImage


class ServiceImageInline(GalleryInline):
    model = ServiceImage


class ServiceInline(admin.TabularInline):
    form = ServiceAdminForm
    model = Service
    fields = ("name", "rank", "slug", "summary", "description", "image", "starting_price", "is_active", "is_featured")
    extra = 0
    show_change_link = True
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "rank", "service_count", "is_active")
    list_editable = ("rank",)
    list_filter = ("is_active", "robots_index", "include_in_sitemap")
    search_fields = ("name", "description", "meta_title", "focus_keyword")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryImageInline, ServiceInline)
    fieldsets = (
        ("Category details", {"fields": ("name", "slug", "description", "rank", "is_active")}),
        ("Main image", {"fields": ("image", "image_alt")}),
    ) + SEO_FIELDSETS

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_service_count=Count("services"))

    @admin.display(description="Services", ordering="_service_count")
    def service_count(self, obj):
        return obj._service_count


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ("name", "category", "rank", "starting_price", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured", "robots_index", "include_in_sitemap")
    list_editable = ("rank", "is_active", "is_featured")
    search_fields = ("name", "summary", "description", "category__name", "meta_title", "focus_keyword")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    inlines = (ServiceImageInline,)
    fieldsets = (
        ("Service details", {"fields": ("category", "name", "slug", "summary", "description", "rank")}),
        ("Main image", {"fields": ("image", "image_alt")}),
        ("Pricing and timing", {"fields": ("starting_price", "estimated_duration", "schema_service_type")}),
        ("Visibility", {"fields": ("is_active", "is_featured")}),
    ) + SEO_FIELDSETS


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "area", "status", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "email", "phone", "area", "message")
    readonly_fields = ("created_at",)
    list_select_related = ("service",)


@admin.register(HomeSlide)
class HomeSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    readonly_fields = ("image_preview",)
    fields = ("title", "subtitle", "image", "image_preview", "alt_text",
              "button_label", "button_url", "sort_order", "is_active")

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" alt="" style="max-width:400px;max-height:180px">', obj.image.url)
        return "No image"

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "service_name", "location", "rating", "sort_order", "is_published")
    list_editable = ("sort_order", "is_published")
    list_filter = ("is_published", "rating")
    search_fields = ("customer_name", "location", "service_name", "review")
    readonly_fields = ("created_at", "updated_at")
    fields = ("customer_name", "location", "service_name", "rating", "review", "sort_order", "is_published", "created_at", "updated_at")
