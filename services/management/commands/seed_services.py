from django.core.management.base import BaseCommand
from services.models import Category, Service


CATALOGUE = [
    ("AC Maintenance", "ac-maintenance", "Keep your home comfortable.", [
        ("AC servicing", "ac-servicing", "Cleaning and maintenance for your air conditioner.", "Filter cleaning, airflow checks and routine maintenance. Any replacement parts are quoted separately.", "1–2 hours"),
    ]),
    ("Plumbing", "plumbing", "Help with everyday water and drainage problems.", [
        ("Plumbing repairs", "plumbing-repairs", "Help with leaking taps, blocked drains and fixtures.", "Inspection and repair of common plumbing problems. Final scope and price depend on the inspection.", "1–3 hours"),
    ]),
    ("Electrical", "electrical", "Electrical repairs and installations.", [
        ("Electrical repairs", "electrical-repairs", "Support for lighting, switches and socket issues.", "Assessment and repair of common household electrical faults. Materials are quoted separately.", "1–2 hours"),
    ]),
    ("Carpentry", "carpentry", "Care for furniture, doors and fittings.", [
        ("Furniture assembly", "furniture-assembly", "Assembly of flat-pack furniture and household fittings.", "Assembly based on your furniture instructions. Share the item type and quantity when requesting a quote.", "1–4 hours"),
        ("Door and cabinet repairs", "door-cabinet-repairs", "Repair loose hinges, sticking doors and cabinet fittings.", "Inspection and adjustment of doors, cabinets and hardware. Replacement fittings are quoted separately.", "1–3 hours"),
    ]),
    ("Painting", "painting", "Refresh your rooms and walls.", [
        ("Interior painting", "interior-painting", "Wall painting and touch-ups for your home.", "Room preparation, minor surface repair and interior painting. The quote depends on area, condition and paint selection.", ""),
    ]),
    ("Cleaning", "cleaning", "Cleaning for living spaces.", [
        ("Home cleaning", "home-cleaning", "General cleaning for apartments and villas.", "Cleaning scope and frequency can be agreed before work begins. The quote depends on property size and requirements.", ""),
    ]),
]



CATALOGUE.append((
    "Moving & Shifting", "moving-shifting",
    "Plan home shifting, office relocation, packing and furniture handling in Qatar.",
    [
        ("House & apartment shifting", "house-apartment-shifting",
         "Plan your apartment or villa move in Qatar with clear access and item details.",
         "House shifting starts with a practical inventory of rooms, furniture and packed boxes. Share pickup and delivery locations, floor levels, lift access and parking arrangements. Discuss packing, dismantling and reassembly requirements before the scope and price are agreed. Fragile or oversized items need to be identified in advance.", "Depends on inventory and access"),
        ("Office relocation", "office-relocation",
         "Organise desks, storage and furniture for a workspace move in Qatar.",
         "Office relocation planning includes an item list, collection and delivery locations, permitted access hours and loading arrangements. Identify desks or storage units needing dismantling and agree on who will handle computers, cabling and sensitive records. Work scope, specialist handling and schedule are confirmed during the quote review.", "Depends on office size"),
        ("Packing & unpacking", "packing-unpacking",
         "Request packing support for household or office belongings.",
         "Packing and unpacking can be included in a moving enquiry or requested separately. Share the approximate quantity of belongings and identify fragile items. Discuss boxes, protective wrapping, labelling and whether materials are included in the quote. Keep valuables and essential documents with you.", "Depends on item volume"),
        ("Furniture dismantling & reassembly", "furniture-dismantling-reassembly",
         "Plan furniture handling before and after a move.",
         "Share the furniture type, quantity and assembly instructions where available. Discuss which items need dismantling, how fittings should be labelled and where furniture will be reassembled. Wall fixing, replacement parts and specialist items are reviewed separately before the quote is agreed.", "Depends on furniture and quantity"),
    ],
))

class Command(BaseCommand):
    help = "Add sample categories and quote-only services without overwriting existing records."

    def handle(self, *args, **options):
        created = 0
        for name, slug, description, items in CATALOGUE:
            category, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "description": description}
            )
            for title, service_slug, summary, detail, duration in items:
                _, was_created = Service.objects.get_or_create(
                    slug=service_slug,
                    defaults={"category": category, "name": title, "summary": summary,
                              "description": detail, "estimated_duration": duration},
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Added {created} services. Existing records preserved."))
