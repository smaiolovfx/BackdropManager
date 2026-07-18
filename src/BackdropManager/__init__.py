"""BackdropManager package entry point.

Copy or symlink ``src/BackdropManager`` to ``~/.nuke/BackdropManager`` and add
this to ``~/.nuke/menu.py``:

import BackdropManager
"""

from .info import __date__, __version__

__all__ = ["__date__", "__version__", "nuke_setup", "setup"]

def setup():
    "Register BackdropManager menus and panels in Nuke."
    from .menu import setup as _setup
    return _setup()

nuke_setup = setup

try:
    import nuke # noqa: F401
except ImportError:
    pass
else:
    setup()