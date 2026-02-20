"""
ASGI config for django_leeway project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import configparser
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opendrift_leeway_webgui.core.settings")

# Read config from config file
config = configparser.ConfigParser(interpolation=None)
config.read("/etc/opendrift-leeway-webgui.ini")
for section in config.sections():
    for key, value in config.items(section):
        os.environ.setdefault(f"LEEWAY_{key.upper()}", value)

application = get_asgi_application()
