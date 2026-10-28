import re
import bleach
from django import template
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

TAGS = ["p", "br", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s",
        "ul", "ol", "li", "blockquote", "a", "img", "figure", "figcaption",
        "table", "thead", "tbody", "tr", "th", "td", "hr", "pre", "code"]
ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "width", "height"],
    "figure": ["class"], "table": ["class"],
    "td": ["colspan", "rowspan"], "th": ["colspan", "rowspan"],
}


@register.filter
def richtext(value):
    value = str(value or "")
    if not re.search(r"</?[a-zA-Z][^>]*>", value):
        value = linebreaks(value, autoescape=True)
    cleaned = bleach.clean(value, tags=TAGS, attributes=ATTRIBUTES,
                           protocols=["http", "https", "mailto", "tel"], strip=True)
    return mark_safe(cleaned)
