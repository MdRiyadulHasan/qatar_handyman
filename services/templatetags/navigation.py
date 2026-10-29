from django import template
from django.db.models import Prefetch
from services.models import Category, Service

register = template.Library()


@register.inclusion_tag("services/_navbar.html", takes_context=True)
def navigation_header(context):
    categories = Category.objects.filter(is_active=True).only("name", "slug", "rank").prefetch_related(
        Prefetch("services", queryset=Service.objects.filter(is_active=True).only(
            "name", "slug", "category_id", "rank"
        ), to_attr="nav_services")
    )
    request = context.get("request")
    return {
        "nav_categories": categories,
        "nav_section": context.get("nav_section", ""),
        "is_home": request is not None and request.path == "/",
    }
