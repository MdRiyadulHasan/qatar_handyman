"""Apply the requested service-copy refresh without changing URLs or prices."""
import json
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.html import format_html, format_html_join
from services.models import Service
from services.service_copy import ENQUIRY_AREAS, SERVICE_COPY


def bullet_section(title, items):
    return str(format_html("<h3>{}</h3><ul>{}</ul>", title,
                          format_html_join("", "<li>{}</li>", ((item,) for item in items))))


class Command(BaseCommand):
    help = "Preview or apply the Qatar service-copy refresh, backing up edited database fields first."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--backup-dir", default=str(settings.BASE_DIR / "content_backups"))

    def handle(self, *args, **options):
        fields = ["id", "slug", "seo_heading", "meta_title", "meta_description", "summary", "description", "service_area", "faqs"]
        with transaction.atomic():
            services = list(Service.objects.select_for_update().filter(slug__in=SERVICE_COPY))
            if not options["apply"]:
                for service in services:
                    self.stdout.write(f"{service.slug}: {SERVICE_COPY[service.slug]['heading']}")
                self.stdout.write(f"Preview: {len(services)} services. Run with --apply to save.")
                return
            if not services:
                self.stdout.write("No matching services; nothing changed.")
                return
            backup_dir = Path(options["backup_dir"])
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"service_details_{uuid4().hex}.json"
            backup.write_text(json.dumps([{key: getattr(service, key) for key in fields} for service in services], ensure_ascii=False, indent=2), encoding="utf-8")
            for service in services:
                copy = SERVICE_COPY[service.slug]
                service.seo_heading = copy["heading"]
                service.meta_title = copy["title"]
                service.summary = copy["summary"]
                label = copy["heading"].removesuffix(" in Doha, Qatar")
                service.meta_description = f"{label} in Doha, Qatar. Discuss your requirements in The Pearl-Qatar, Lusail and nearby areas. Request a tailored quote from Qatar Move & Fix."
                service.description = "".join([
                    bullet_section("What you can request", copy["scope"]),
                    bullet_section("Suitable spaces & projects", copy["spaces"]),
                    bullet_section("Details for an accurate quote", copy["prepare"]),
                    bullet_section("Before work begins", ["Confirm scope, materials, access and the final price before booking.", "Share your exact location so availability and any travel requirements can be confirmed."]),
                ])
                if not service.service_area:
                    service.service_area = ", ".join(ENQUIRY_AREAS)
                if not service.faqs:
                    service.faqs = [
                        {"question": f"Can I request {label.lower()} in my area?", "answer": "Send your location pin in Doha, The Pearl-Qatar, Lusail, Al Wakrah, Al Rayyan or Al Khor. The team will confirm access, travel requirements and availability before booking."},
                        {"question": f"What affects the price of {label.lower()}?", "answer": "The quote depends on the work involved, measurements or item quantity, materials, access and transport needs. Share photos and your preferred date so the scope and final price can be reviewed."},
                    ]
                service.full_clean()
                service.save(update_fields=[field for field in fields if field not in {"id", "slug"}] + ["updated_at"])
        self.stdout.write(self.style.SUCCESS(f"Updated {len(services)} services. Original fields backed up to {backup}."))
