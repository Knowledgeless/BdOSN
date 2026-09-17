import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BdOSN.settings")

from BdOSN.wsgi import application

app = application
