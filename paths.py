"""Filesystem paths used by BackdropManager."""

import os

PACKAGE_DIR = os.path.dirname(__file__)
ICON_DIR = os.path.join(PACKAGE_DIR, "icons")


def icon_path(icon_name):
    """Return the path to an icon file."""
    return os.path.join(ICON_DIR, icon_name)
