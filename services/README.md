# Qatar Move & Fix services

Premium responsive Django website for home maintenance and moving enquiries.

## Pages

- / — home
- /services/ — searchable, paginated catalogue
- /services/moving-shifting/ — moving and shifting landing page
- /services/about/ — approach
- /services/areas/ — location and access guidance
- /services/faq/ — FAQs
- /services/contact/ — quote request form
- /services/<slug>/ — individual service details
- /sitemap.xml and /robots.txt — crawl discovery

## Setup

MySQL is the default database. Follow ../MYSQL_SETUP.md to install dependencies,
configure .env and create the database before these commands.

    python manage.py migrate
    python manage.py seed_services
    python manage.py createsuperuser
    python manage.py runserver

The seed command adds sample services, including four moving services, without
overwriting existing records. All sample prices are quote-only. Manage categories,
services, featured flags, prices and per-service SEO fields in Django admin.
Quote requests are stored in admin under Inquiries; no emails, messages, payments
or bookings are sent or confirmed automatically.

## SEO

Every content page has a distinct title and description, canonical URL,
Open Graph metadata and server-rendered content. Service pages include Service
and BreadcrumbList JSON-LD with script-safe serialization. Search/filter pages
use noindex,follow. Paginated catalogue pages use their own canonicals.
The sitemap contains public pages plus active, indexable services and category pages with their own canonical URLs.

The public origin defaults to https://qatarmoveandfix.com. Canonical URLs,
Open Graph URLs, structured data, robots.txt and sitemap.xml use this origin.
Set SITE_URL in .env to override it; set SITE_URL= for request-based local URLs.
ALLOWED_HOSTS accepts the bare domain, www domain, localhost and loopback by
default. Override ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS with comma-separated
values if your hosting environment requires additional hosts or origins.

Deploy the updated code to your host, point both domain names to that host,
install an HTTPS certificate and redirect www to https://qatarmoveandfix.com
in the web server. Configure production DEBUG and secret-key settings before
hosting. Existing administrator-written slide text and SEO overrides remain
editable in Django admin; review them for the new business name/domain.

Guidance: https://developers.google.com/search/docs/fundamentals/get-started-developers

## Verify

    python manage.py check
    python manage.py test services

## Category and service photos

Edit a category or service in Django admin. Choose a main image and its alt text.
Use the gallery inline rows and Add another to attach any number of additional
photos in one save. Each photo supports alt text, a caption, display order and an
active flag. JPG/JPEG, PNG and WebP files up to 10 MB are supported. Image uploads
are validated by Pillow through Django ImageField forms.

Service cards show the service main image, falling back to the category main
image. Service details show the main photo and active gallery photos. Select a
category in the catalogue to see its main photo and gallery. Gallery links open
full-size images. Existing records can keep their images blank.

Uploaded files are stored under media/, and MySQL stores their file paths.
Development URLs serve these files when DEBUG is enabled. When going live,
configure the host or object storage to serve MEDIA_URL and transfer the media
files alongside the database; database exports do not include image contents.
Replacing or deleting an image record does not remove the file automatically.
### Project media folders

New uploads save under MEDIA_ROOT (the project's media folder):

- media/categories/covers/YYYY/MM/ — category main images
- media/categories/gallery/YYYY/MM/ — category gallery images
- media/services/covers/YYYY/MM/ — service main images
- media/services/gallery/YYYY/MM/ — service gallery images

Existing uploads keep their stored paths and remain accessible. Upload through
/admin/ by editing a category or service and saving its image fields/gallery.
Django stores files automatically; templates use image.url to build /media/ links.
Putting a file into media manually does not create a category/gallery record.
Run python manage.py runserver for local media serving. For live hosting, serve
/media/ through your web server or configured media storage, and transfer both
the database and uploaded files. Keep media uploads out of Git.
## Homepage slider and grouped services

Homepage order: image slider, all active categories, then all active services
under each category. Each service card links to its existing detail page. Empty
active categories remain visible. Inactive categories and services are hidden.

The homepage slider reads active HomeSlide records from /admin/services/homeslide/.
Each record supplies its own title, subtitle, image, alt text, button label and URL.
Sort order (then record ID) controls the sequence. These images are independent of
category card images. Set the button URL to a category page to link to its services;
blank button URLs open the full catalogue. Inactive slides and records without an
image are excluded. With no active slides, a neutral contact slide appears.
Single-slide carousels do not show playback controls.

Slides rotate every four seconds. Controls support previous/next, slide selectors,
play/pause, arrow keys and horizontal touch swipes. Automatic rotation pauses while
hovered/focused or while the tab is hidden. Reduced-motion users start with rotation
paused. The first slide remains available without JavaScript.

## CKEditor descriptions

Category and Service descriptions use CKEditor 5 in Django admin, including
headings, emphasis, links, lists, tables and image uploads. No description column
conversion is required. Old plain-text descriptions continue to display with
paragraphs/line breaks; rich HTML is sanitized before rendering publicly.
Uploads are staff-only, limited to 10 MB JPG/PNG/WebP, and saved in media/editor/.

The bundled editor requires a license mode. The configuration defaults to GPL;
set CKEDITOR_5_LICENSE_KEY in your environment for your own commercial license.
Choose the license appropriate to the project before distributing it or going
live: https://ckeditor.com/docs/ckeditor5/latest/getting-started/licensing/license-key-and-activation.html

Verification includes server-rendered ordering/grouping, hidden content, slide
ordering, editor widget assets, staff-only uploads and rich-text sanitization.
Visual browser and carousel interaction checks require an available browser.

## Category and service SEO fields

Edit categories and services in Django admin. Existing meta_title, meta_description,
slug, image and image_alt fields continue to work. Blank optional overrides fall
back to the existing content. New shared columns are:

- seo_heading: page H1; breadcrumb_title: short visible/schema breadcrumb label.
- focus_keyword: internal editorial planning, not an HTML keywords meta tag.
- canonical_url: optional absolute HTTP(S) URL; blank uses the page's own URL.
- robots_index, robots_follow, robots_max_snippet, robots_max_image_preview:
  indexing, links and search preview controls. Search queries remain noindex.
- include_in_sitemap: opt out of discovery without hiding the public page.
  Inactive/noindex pages and pages canonicalized elsewhere are excluded automatically.
- og_title, og_description, social_image, social_image_alt: Open Graph previews.
- twitter_title, twitter_description, twitter_card: X/Twitter preview overrides;
  images are shared with Open Graph. Cover/gallery photography is the fallback.
- service_area: actual locations separated by commas; services inherit the category
  area for structured data when blank, then fall back to Qatar.
- faqs: validated JSON list of {"question": "...", "answer": "..."} plain-text
  objects. These appear visibly on the page and in escaped FAQ structured data.
  Structured data does not guarantee a search feature or ranking.

Services additionally have schema_service_type, defaulting to the category name.
Existing starting prices supply QAR minimum-price structured data; no ratings or
reviews are invented. Categories now also have created_at and updated_at timestamps.

Category pages use /services/category/<slug>/. Old ?category=<slug> filters still
work and point their canonical metadata to the category page. Navigation, slider,
and category links use the dedicated URLs. Pagination has page-specific canonicals
unless an explicit canonical override was entered. Run python manage.py migrate
on each deployment before serving requests with these models.


## Customer reviews

Run `python manage.py migrate` after deploying. Manage feedback at
`/admin/services/customerreview/`: add a customer name, rating (1-5), actual
review, and optionally a location and service name. Reviews start unpublished.
Enable "Is published" to display a review on the homepage. Use "Sort order"
to control placement (lower first); ties show the most recently added first.
Unpublish or delete a review to remove it from the homepage. No sample reviews
are created; an invitation to share feedback appears until reviews are published.


## Structured service details

Service descriptions support headings and bullet lists in the existing rich-text
editor. Page title, H1, description, FAQs and comma-separated locations stay
editable in Django admin. Pages show readable location chips, a quote panel,
preparation steps, related services and FAQs. Blank coverage fields show suggested
enquiry areas visibly while structured data retains the Qatar country fallback.

`python manage.py update_service_details` previews the supplied 12-service copy.
Use `--apply` to save it. Before any update, the command backs up the edited fields
under `content_backups/` (excluded from Git). Reapplying replaces those copy fields;
URLs, service names, images and prices are preserved. Existing non-empty service
areas and FAQs are preserved. The saved JSON contains the prior values by ID/slug
for recovery or comparison; it is not a Django fixture.


## Google Search launch and local SEO

The homepage uses the first slider title as its single H1, with social metadata,
and Organization/WebSite structured data using the actual brand, logo and phone.
Service/category metadata remains database-managed. Demo reviews stay labeled;
no review ratings or fabricated addresses are included in structured data.

Before requesting Google indexing:

1. Deploy to https://qatarmoveandfix.com with working HTTPS. Redirect the www
   domain to the bare domain, and HTTP to HTTPS, through your hosting server.
2. Configure production Django settings (DEBUG=False, a private secret key and
   web-server static/media serving). Current development settings are not a
   completed production deployment.
3. Verify domain ownership in Google Search Console using its DNS method, or set
   GOOGLE_SITE_VERIFICATION to the HTML-tag content token in the deployed .env.
   The HTML token verifies a URL-prefix property; it does not verify the DNS
   domain property. No token or account is provisioned automatically.
4. Submit https://qatarmoveandfix.com/sitemap.xml in Search Console. Inspect the
   homepage and key service URLs, then request indexing where appropriate.
5. Create/verify a Google Business Profile with truthful service areas, business
   category, phone, hours and business details. Ask real customers for feedback;
   replace demonstration reviews before launch.
6. Monitor indexing, search queries and mobile performance in Search Console and
   PageSpeed Insights. Keep service descriptions and genuine project photos current.

Google controls crawling, indexing and rankings. A sitemap or city keyword does
not guarantee indexing or a top position. Local visibility also depends on
relevance, distance and prominence; no business address or opening hours should
be invented for search markup.

References:
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://developers.google.com/search/docs/appearance/structured-data/organization
- https://support.google.com/business/answer/7091


## cPanel production setup and collectstatic

The deployment requirement is pinned to Django 5.0.6 at the owner's request.
Choose Python 3.12 in cPanel's Setup Python App; Django 5.0 officially supports
Python 3.10-3.12. Django 5.0 is unsupported and no longer receives security fixes;
plan a supported upgrade with the hosting provider. Set the application root to a private directory,
for example `/home/CPANEL_USERNAME/qatar_move_fix`; startup file is
`passenger_wsgi.py` and entry point is `application`. Set DJANGO_DEBUG=False in .env. The startup file defaults
to DEBUG=False and refuses to boot without a private production SECRET_KEY.
Keep the cPanel-generated virtual environment and Passenger configuration.

Upload qatar_handyman/, services/, manage.py, requirements.txt and
passenger_wsgi.py to that app root. Create .env there from .env.example, replace
the database/user/password placeholders and generate a private key once:

    python -c "import secrets; print(secrets.token_urlsafe(64))"

Set STATIC_ROOT and MEDIA_ROOT to dedicated directories inside the actual domain
document root, for example (replace CPANEL_USERNAME and verify the document root
in cPanel Domains; addon domains may use a different path):

    STATIC_ROOT=/home/CPANEL_USERNAME/public_html/static
    MEDIA_ROOT=/home/CPANEL_USERNAME/public_html/media

The web server must map /static/ to STATIC_ROOT and /media/ to MEDIA_ROOT. If the
host's Passenger rules route those paths to Django, ask the host to exclude them
or configure the static mappings. Uploaded files must be served without script
execution; keep directory listing disabled. Python code, .env and backups stay
outside the public document root. Copy the CONTENTS of the existing media/ into
the configured MEDIA_ROOT to preserve existing database image paths. Never
collectstatic into media; collection does not copy customer uploads.

Activate the environment using the exact command cPanel provides, change into
the private app root, then run these commands in that environment:

    python -m pip install -r requirements.txt
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    python manage.py check --deploy

Create a superuser only if your imported database has no admin account. Existing
local content/reviews require a database export/import in addition to migrate;
migrate creates tables but does not copy your local records. mysqlclient needs
the host's MySQL client libraries if no compatible binary wheel is available.

Restart the application in cPanel. Check the homepage, admin login, CSS and images,
including /static/services/styles.css, /static/admin/css/base.css and a real
/media/ image. Enable the domain HTTPS certificate before public launch. The
security defaults use HTTPS redirection and secure cookies with DEBUG=False;
if a proxy causes redirect loops, confirm its configuration with the host before
enabling TRUST_X_FORWARDED_PROTO. HSTS defaults to one hour for the current host,
with subdomain inclusion and preload disabled.

For later code updates: back up the live database and media, upload changed source,
install dependencies if changed, migrate if needed, collectstatic when static
assets change, then restart Passenger. Keep the server .env, private key, live
records and uploads. Do not use collectstatic --clear on a directory containing
anything except collected static output.

Without STATIC_ROOT in .env, local `python manage.py collectstatic --noinput`
collects into the project's staticfiles/ directory (ignored by Git). Upload its
CONTENTS into the domain's /static/ folder if collecting locally, or run the
command directly on the server with STATIC_ROOT set as shown above. Django does
not serve these files itself in production, and uploading staticfiles/ alone
without a URL mapping does not enable public static serving.

References:
- https://docs.djangoproject.com/en/5.0/howto/static-files/deployment/
- https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- https://docs.cpanel.net/knowledge-base/web-services/how-to-install-a-python-wsgi-application/

`check --deploy` may report security.W005 and security.W021 because HSTS for all
subdomains and browser preload are intentionally disabled. Enable neither until
all relevant domains permanently support HTTPS. Resolve other warnings before
launch. Django 5.0 still requires MySQL 8.0.11+ or MariaDB 10.4+. Downgrading
Django does not add MySQL 5.7 support. Check the actual database version in cPanel
or phpMyAdmin before deployment. Static collection and Passenger configuration
remain available with this pin.


## Current local development configuration

The ignored root `.env` uses the existing local MySQL database `qatar_handyman`
at 127.0.0.1, local development credentials, DJANGO_DEBUG=True and
SITE_URL=http://127.0.0.1:8000. Start with `python manage.py runserver` and visit
http://127.0.0.1:8000/. HTTP is allowed locally; secure cookies and HTTPS redirects
remain enabled by default in production. A blank MySQL password is allowed only
in debug mode; production still requires a database username and password.

The ignored `.env.cpanel` is a separate production file. Upload only that file
as `.env` in the private server app root, after verifying the hosting username,
password and document-root paths. Do not replace the local `.env` with it when
working on your computer. cPanel database settings and records were not changed.
