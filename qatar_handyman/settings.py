import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be True or False.")


# Local runserver defaults to development; Passenger defaults to production.
DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-")):
    raise ImproperlyConfigured("Set a private SECRET_KEY of at least 50 characters before using DEBUG=False.")
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-local-development-only-do-not-use-in-production"

ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    "ALLOWED_HOSTS", "qatarmoveandfix.com,www.qatarmoveandfix.com,localhost,127.0.0.1,[::1]"
).split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "https://qatarmoveandfix.com,https://www.qatarmoveandfix.com"
).split(",") if origin.strip()]


# HTTPS defaults are enabled in production and disabled for local development.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0" if DEBUG else "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# Enable only when the host strips untrusted headers and sets this header itself.
if env_bool("TRUST_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'services.apps.ServicesConfig',
    'django_ckeditor_5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qatar_handyman.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'qatar_handyman.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").lower()

if DB_ENGINE == "mysql":
    missing_db_settings = [name for name in ("DB_USER", "DB_PASSWORD") if not os.environ.get(name, "").strip()] if not DEBUG else []
    if missing_db_settings:
        raise ImproperlyConfigured(
            "Set " + ", ".join(missing_db_settings) + " in the private .env file or cPanel application environment."
        )
    # DATABASES = {
    #     "default": {
    #         "ENGINE": "django.db.backends.mysql",
    #         "NAME": os.environ.get(
    #             "DB_NAME", "qatar_handyman" if DEBUG else "qatarmov_qatar_handyman"
    #         ),
    #         "USER": os.environ.get("DB_USER", "root" if DEBUG else ""),
    #         "PASSWORD": os.environ.get("DB_PASSWORD", ""),
    #         "HOST": os.environ.get("DB_HOST", "127.0.0.1" if DEBUG else "localhost"),
    #         "PORT": os.environ.get("DB_PORT", "3306"),
    #         "OPTIONS": {
    #             "charset": "utf8mb4",
    #             "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    #             "isolation_level": "read committed",
    #             "connect_timeout": 5,
    #         },
    #     }
    # }
    # DATABASES = {
    #         "default": {
    #             "ENGINE": "django.db.backends.mysql",
    #             "NAME": "qatar_handyman",
    #             "USER": "root",
    #             "PASSWORD": "",
    #             "HOST": "localhost",
    #             "PORT": "3306",
    #         }
    #     }
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "qatarmov_qatar_handyman",
            "USER": "qatarmov_ayesha",
            "PASSWORD": "ayesha1@34",
            "HOST": "localhost",
            "PORT": "3306",
        }
    }
elif DB_ENGINE == "sqlite":
    # Explicit opt-in for local testing or exporting the previous catalogue.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE must be either 'mysql' or 'sqlite'.")



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# STATIC_URL = "/static/"
# STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", "").strip() or BASE_DIR / "staticfiles").expanduser()
# if not STATIC_ROOT.is_absolute():
#     STATIC_ROOT = BASE_DIR / STATIC_ROOT

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Public HTTPS origin for canonical URLs and sitemap. Explicitly blank uses the request origin.
# SITE_URL = os.environ.get("SITE_URL", "https://qatarmoveandfix.com").rstrip("/")

# MEDIA_URL = "/media/"
# MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "").strip() or BASE_DIR / "media").expanduser()
# if not MEDIA_ROOT.is_absolute():
#     MEDIA_ROOT = BASE_DIR / MEDIA_ROOT

# # Collection output must not overlap source files or uploaded customer media.
# _static_root = STATIC_ROOT.resolve()
# _media_root = MEDIA_ROOT.resolve()
# if _static_root == BASE_DIR.resolve() or _static_root in BASE_DIR.resolve().parents:
#     raise ImproperlyConfigured("STATIC_ROOT must be a dedicated output directory, not the project root or its parent.")
# if _static_root == _media_root or _static_root in _media_root.parents or _media_root in _static_root.parents:
#     raise ImproperlyConfigured("STATIC_ROOT and MEDIA_ROOT must be separate, non-overlapping directories.")

# CKEditor descriptions and staff-only image uploads.
CKEDITOR_5_CONFIGS = {
    "default": {
        "licenseKey": os.environ.get("CKEDITOR_5_LICENSE_KEY", "GPL"),
        "toolbar": {
            "items": ["heading", "|", "bold", "italic", "link", "|",
                      "bulletedList", "numberedList", "blockQuote", "|",
                      "insertTable", "uploadImage", "|", "undo", "redo"],
            "shouldNotGroupWhenFull": True,
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
            ]
        },
        "image": {"toolbar": ["imageTextAlternative", "toggleImageCaption"]},
        "table": {"contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"]},
    }
}
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_FILE_STORAGE = "services.editor_storage.EditorImageStorage"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpg", "jpeg", "png", "webp"]
CKEDITOR_5_MAX_FILE_SIZE = 10


# Optional HTML verification token supplied by Google Search Console.
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()

STATIC_URL = "/static/"
STATIC_ROOT = "/home/qatarmov/public_html/static"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Website URL
SITE_URL = os.environ.get("SITE_URL", "https://qatarmoveandfix.com").rstrip("/")

# Media files (Images, Uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = "/home/qatarmov/public_html/media"