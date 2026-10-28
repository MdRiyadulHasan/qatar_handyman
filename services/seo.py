import json
from urllib.parse import urlencode, urljoin
from django.conf import settings
from django.urls import reverse


def absolute_url(request, path):
    origin = getattr(settings, "SITE_URL", "").rstrip("/")
    return urljoin(origin + "/", path) if origin else request.build_absolute_uri(path)


def json_ld(data):
    # Escape HTML delimiters so administrator-written content cannot close a script.
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


class SEOMixin:
    seo_title = "Qatar Move & Fix | Moving, Shifting & Home Maintenance Services in Qatar"
    seo_description = "Explore home repairs, maintenance and moving services in Qatar. Find the right service and send a request for a tailored quote."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.request.path
        if context.get("page_obj") and context["page_obj"].number > 1:
            path += "?" + urlencode({"page": context["page_obj"].number})
        canonical = absolute_url(self.request, path)
        context.update(
            seo_title=self.seo_title, seo_description=self.seo_description,
            canonical_url=canonical,
            robots="noindex,follow" if self.request.GET.get("q") or self.request.GET.get("category") else "index,follow",
            nav_section=getattr(self, "nav_section", ""),
            google_site_verification=getattr(settings, "GOOGLE_SITE_VERIFICATION", ""),
            schema_json=json_ld({
                "@context": "https://schema.org", "@type": "WebPage",
                "name": self.seo_title, "description": self.seo_description, "url": canonical,
                "isPartOf": {"@type": "WebSite", "name": "Qatar Move & Fix",
                             "url": absolute_url(self.request, reverse("home"))},
            }),
        )
        return context


def apply_object_seo(request, context, obj, title, description):
    """Apply shared per-record metadata, keeping search result pages noindex."""
    from django.utils.html import strip_tags
    from django.utils.text import Truncator
    page = context.get("page_obj")
    page_number = page.number if page else 1
    path = obj.get_absolute_url()
    if page_number > 1:
        path += "?" + urlencode({"page": page_number})
    canonical = obj.canonical_url or absolute_url(request, path)
    title = obj.meta_title or title
    if page_number > 1:
        title += f" | Page {page_number}"
    description = obj.meta_description or Truncator(strip_tags(description)).chars(300)
    photo = obj.card_photo
    image = absolute_url(request, obj.social_image.url if obj.social_image else photo["url"])
    image_alt = obj.social_image_alt or photo["alt"]
    directives = ["index" if obj.robots_index and not request.GET.get("q") else "noindex",
                  "follow" if obj.robots_follow else "nofollow"]
    directives += [f"max-snippet:{obj.robots_max_snippet}", f"max-image-preview:{obj.robots_max_image_preview}"]
    context.update(
        seo_title=title, seo_description=description, canonical_url=canonical,
        robots=",".join(directives), seo_heading=obj.seo_heading or obj.name,
        og_title=obj.og_title or title, og_description=obj.og_description or description,
        seo_image=image, seo_image_alt=image_alt,
        twitter_title=obj.twitter_title or obj.og_title or title,
        twitter_description=obj.twitter_description or obj.og_description or description,
        twitter_card=obj.twitter_card, page_faqs=obj.faqs,
        page_service_area=obj.service_area,
    )


def breadcrumb_schema(request, items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": index, "name": name, "item": absolute_url(request, url)}
        for index, (name, url) in enumerate(items, 1)
    ]}


def faq_schema(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": item["question"],
         "acceptedAnswer": {"@type": "Answer", "text": item["answer"]}}
        for item in faqs
    ]}


def sitemap_url(request, obj):
    """Return only the local, canonical, indexable page URL."""
    url = absolute_url(request, obj.get_absolute_url())
    if not obj.robots_index or not obj.include_in_sitemap:
        return None
    if obj.canonical_url and obj.canonical_url != url:
        return None
    return url
