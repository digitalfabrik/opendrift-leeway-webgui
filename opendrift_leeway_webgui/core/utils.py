"""
Utilities for the opendrift leeway webgui core application
"""

BOOLEAN_MAP = {
    "y": True,
    "yes": True,
    "t": True,
    "true": True,
    "on": True,
    "1": True,
    "n": False,
    "no": False,
    "f": False,
    "false": False,
    "off": False,
    "0": False,
}


def strtobool(value):
    """
    Convert a boolean string to a boolean
    """
    try:
        return BOOLEAN_MAP[str(value).lower()]
    except KeyError as exc:
        raise ValueError(f'"{value}" is not a valid bool value') from exc
