#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import configparser
import os
import sys


def read_config():
    """
    Reads and parses the corresponding configurations.
    """
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "opendrift_leeway_webgui.core.settings"
    )

    # Read config from config file
    config = configparser.ConfigParser(interpolation=None)
    config.read("/etc/opendrift-leeway-webgui.ini")
    for section in config.sections():
        for KEY, VALUE in config.items(section):
            os.environ.setdefault(f"LEEWAY_{KEY.upper()}", VALUE)


def main():
    """Run administrative tasks."""
    read_config()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
