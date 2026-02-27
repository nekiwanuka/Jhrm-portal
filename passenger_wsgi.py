import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / '.env')
os.environ['DJANGO_SETTINGS_MODULE'] = os.getenv('DJANGO_SETTINGS_MODULE', 'hrms.settings.prod')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
