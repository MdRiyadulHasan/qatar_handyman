import re
from xml.etree.ElementTree import Element, SubElement, tostring
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.http import HttpResponse, Http404
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView
from .content import AREAS, FAQS, PAGES
from .forms import InquiryForm
from .service_copy import ENQUIRY_AREAS
from .models import Category, CategoryImage, CustomerReview, HomeSlide, Service, ServiceImage
from .seo import (SEOMixin, absolute_url, json_ld, apply_object_seo,
                  breadcrumb_schema, faq_schema, sitemap_url)


def public_services():
    return Service.objects.select_related("category").filter(is_active=True, category__is_active=True).prefetch_related(
        Prefetch("images", queryset=ServiceImage.objects.filter(is_active=True), to_attr="active_gallery_images"),
        Prefetch("category__images", queryset=CategoryImage.objects.filter(is_active=True), to_attr="active_gallery_images"),
    )


class HomeView(SEOMixin, TemplateView):
    template_name = "services/home.html"
    nav_section = "home"
    seo_title = "Moving & Home Maintenance in Qatar | Qatar Move & Fix"
    seo_description = "Moving, shifting, carpentry, painting, gypsum, curtain and carpet installation in Qatar. Enquire from Doha, Lusail and The Pearl-Qatar for a tailored quote."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Category.objects.filter(is_active=True).prefetch_related(
            Prefetch("images", queryset=CategoryImage.objects.filter(is_active=True), to_attr="active_gallery_images"),
            Prefetch("services", queryset=public_services(), to_attr="home_services")
        )
        slides = [
            {
                "title": slide.title,
                "subtitle": slide.subtitle,
                "image_url": slide.image.url,
                "alt_text": slide.alt_text or slide.title,
                "button_label": slide.button_label,
                "button_url": slide.button_url or reverse("services:list"),
            }
            for slide in HomeSlide.objects.filter(is_active=True).exclude(image="")
        ]
        if not slides:
            slides.append({
                "title": "Your move. Your repairs. One local team.",
                "subtitle": "Qatar Move & Fix brings moving, packing, home repairs and maintenance into one service catalogue. Share your requirements for a tailored quote in Qatar.",
                "image_url": static("services/home-illustration.svg"),
                "alt_text": "Furniture and moving boxes in a home",
                "button_label": "Request a quote",
                "button_url": reverse("services:contact"),
            })
        context.update(home_categories=categories, slides=slides, faqs=FAQS[:3],
                       customer_reviews=CustomerReview.objects.filter(is_published=True))
        home_url = absolute_url(self.request, reverse("home"))
        logo_url = absolute_url(self.request, static("services/qatar-move-and-fix-logo.png"))
        context.update(seo_image=logo_url, seo_image_alt="Qatar Move & Fix logo",
                       twitter_card="summary_large_image")
        context["schema_json"] = json_ld({"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "@id": home_url + "#organization",
             "name": "Qatar Move & Fix", "url": home_url, "logo": logo_url,
             "telephone": "+97466433172", "description": self.seo_description,
             "areaServed": {"@type": "Country", "name": "Qatar"}},
            {"@type": "WebSite", "@id": home_url + "#website",
             "name": "Qatar Move & Fix", "url": home_url,
             "publisher": {"@id": home_url + "#organization"}},
            {"@type": "WebPage", "@id": home_url + "#webpage", "url": home_url,
             "name": self.seo_title, "description": self.seo_description,
             "isPartOf": {"@id": home_url + "#website"},
             "about": {"@id": home_url + "#organization"}},
        ]})

        return context


class ServiceListView(SEOMixin, ListView):
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"
    paginate_by = 12
    nav_section = "services"
    seo_title = "Moving & Home Repair Services | Qatar Move & Fix"
    seo_description = "Browse AC servicing, plumbing, electrical repairs, carpentry, cleaning and moving services in Qatar. Compare service details and request a quote."

    def get_queryset(self):
        queryset = public_services()
        query = self.request.GET.get("q", "").strip()[:200]
        category = self.kwargs.get("slug", self.request.GET.get("category", ""))
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(summary__icontains=query)
                | Q(description__icontains=query) | Q(category__name__icontains=query)
            )
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            categories=Category.objects.filter(is_active=True).prefetch_related(
                Prefetch("images", queryset=CategoryImage.objects.filter(is_active=True), to_attr="active_gallery_images")),
            query=self.request.GET.get("q", "").strip()[:200],
            selected_category=self.kwargs.get("slug", self.request.GET.get("category", "")),
        )
        category = context["categories"].filter(slug=context["selected_category"]).first()
        if self.kwargs.get("slug") and category is None:
            raise Http404("Category not found")
        if category:
            apply_object_seo(self.request, context, category,
                             f"{category.name} | Qatar Move & Fix", category.description or self.seo_description)
            graph = [
                {"@type": "CollectionPage", "name": context["seo_title"],
                 "description": context["seo_description"], "url": context["canonical_url"],
                 "mainEntity": {"@type": "ItemList", "itemListElement": [
                     {"@type": "ListItem", "position": (context["page_obj"].start_index() + index),
                      "name": item.name, "url": absolute_url(self.request, item.get_absolute_url())}
                     for index, item in enumerate(context["services"])
                 ]}},
                breadcrumb_schema(self.request, [("Home", reverse("home")),
                    ("Services", reverse("services:list")),
                    (category.breadcrumb_title or category.name, context["canonical_url"])])
            ]
            if category.faqs:
                graph.append(faq_schema(category.faqs))
            context["schema_json"] = json_ld({"@context": "https://schema.org", "@graph": graph})
        context["category_object"] = category
        context["category_gallery"] = category.images.filter(is_active=True) if category else []
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filter_query"] = params.urlencode()
        if not category and context["page_obj"].number > 1:
            context["seo_title"] += f" | Page {context['page_obj'].number}"
        return context


class CategoryDetailView(ServiceListView):
    """An indexable catalogue page for one active category."""


class ServiceDetailView(SEOMixin, DetailView):
    template_name = "services/service_detail.html"
    context_object_name = "service"
    nav_section = "services"

    def get_queryset(self):
        return public_services()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        context["service_gallery"] = service.images.filter(is_active=True)
        location_title = service.name if re.search(r"\bqatar\b", service.name, re.IGNORECASE) else f"{service.name} in Qatar"
        apply_object_seo(self.request, context, service,
                         f"{location_title} | Qatar Move & Fix", service.summary)
        context["service_heading"] = service.seo_heading or location_title
        area = service.service_area or service.category.service_area
        context["page_service_area"] = area
        context["service_locations"] = [place.strip() for place in area.split(",") if place.strip()] if area else ENQUIRY_AREAS
        service_data = {
            "@type": "Service", "name": service.name, "description": service.summary,
            "url": context["canonical_url"], "image": context["seo_image"],
            "serviceType": service.schema_service_type or service.category.name,
            "areaServed": ([{"@type": "Place", "name": name.strip()} for name in area.split(",") if name.strip()]
                           if area else {"@type": "Country", "name": "Qatar"}),
            "provider": {"@type": "Organization", "name": "Qatar Move & Fix",
                         "url": absolute_url(self.request, reverse("home")), "telephone": "+97466433172"},
        }
        if service.starting_price is not None:
            service_data["offers"] = {"@type": "Offer", "url": context["canonical_url"],
                "priceSpecification": {"@type": "PriceSpecification", "minPrice": str(service.starting_price), "priceCurrency": "QAR"}}
        graph = [service_data, breadcrumb_schema(self.request, [
            ("Home", reverse("home")), ("Services", reverse("services:list")),
            (service.category.breadcrumb_title or service.category.name, service.category.get_absolute_url()),
            (service.breadcrumb_title or service.name, context["canonical_url"])])]
        if service.faqs:
            graph.append(faq_schema(service.faqs))
        context.update(
            related_services=public_services().filter(category=service.category).exclude(pk=service.pk)[:3],
            schema_json=json_ld({"@context": "https://schema.org", "@graph": graph}),
        )
        return context


class MovingView(SEOMixin, TemplateView):
    template_name = "services/moving.html"
    nav_section = "moving"
    seo_title = "House & Office Moving in Qatar | Qatar Move & Fix"
    seo_description = "Plan house shifting, apartment moves, office relocation and packing in Qatar. Share access details and your moving requirements for a tailored quote."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(services=public_services().filter(
            Q(category__slug="moving-shifting") | Q(category__slug="moving-shifting-services-qatar")
        ), faqs=FAQS[:4])
        return context


class InformationView(SEOMixin, TemplateView):
    template_name = "services/information.html"
    page = "about"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title, heading, description = PAGES[self.page]
        context.update(page=self.page, page_heading=heading, seo_title=title,
                       seo_description=description, nav_section=self.page, areas=AREAS, faqs=FAQS)
        context["schema_json"] = json_ld({
            "@context": "https://schema.org", "@type": "WebPage", "name": title,
            "description": description, "url": context["canonical_url"],
        })
        return context


class ContactView(SEOMixin, FormView):
    template_name = "services/contact.html"
    form_class = InquiryForm
    success_url = reverse_lazy("services:contact")
    nav_section = "contact"
    seo_title = "Request a Moving or Repair Quote | Qatar Move & Fix"
    seo_description = "Tell Qatar Move & Fix about your repair, maintenance or moving requirements. Send your location and preferred date for a quote review."

    def get_initial(self):
        initial = super().get_initial()
        slug = self.request.GET.get("service", "")
        service = public_services().filter(slug=slug).first()
        if service:
            initial["service"] = service.pk
        return initial

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your request has been received. The team can review it and contact you using the details provided. This is not a confirmed booking.")
        return super().form_valid(form)


def sitemap(request):
    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for name in ("home", "services:list", "services:moving", "services:about",
                 "services:areas", "services:faq", "services:contact"):
        node = SubElement(root, "url")
        SubElement(node, "loc").text = absolute_url(request, reverse(name))
    for queryset in (Category.objects.filter(is_active=True),
                     Service.objects.filter(is_active=True, category__is_active=True)):
        for obj in queryset.iterator(chunk_size=500):
            url = sitemap_url(request, obj)
            if not url:
                continue
            node = SubElement(root, "url")
            SubElement(node, "loc").text = url
            SubElement(node, "lastmod").text = obj.updated_at.date().isoformat()
    return HttpResponse(tostring(root, encoding="utf-8", xml_declaration=True), content_type="application/xml")


def robots(request):
    text = "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: " + absolute_url(request, reverse("sitemap")) + "\n"
    return HttpResponse(text, content_type="text/plain")
