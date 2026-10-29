"""cPanel/Passenger startup file. Set entry point to application."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
load_dotenv(APP_ROOT / ".env", override=False)
os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qatar_handyman.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
