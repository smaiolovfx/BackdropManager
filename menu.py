"""Nuke menu and panel registration."""

import datetime

import nuke
from nukescripts import panels

from .dag import wrapped
from .dialog_launchers import gui, guiUI
from .info import __date__, __version__
from .operations import snap
from .panel import BackdropPanel
from .settings import Overrides

_REGISTERED = False


def setup():
    """Register BackdropManager commands, shortcuts, and panels."""
    global _REGISTERED
    if _REGISTERED:
        return

    year = datetime.date.today().year
    nuke.tprint(
    "BackdropManager v{0}, built {1}.\n"
    "Copyright (c) 2022-{2} Samantha Maiolo."
    " All Rights Reserved.".format(__version__, __date__, year)
    )

    settings = Overrides()
    data = settings.restore()

    if not nuke.env["gui"]:
        _REGISTERED = True
        return

    nuke.menu("Nuke").addCommand("Edit/Backdrop Manager Settings", gui)
    nuke.menu("Node Graph").addCommand("Create Backdrop", guiUI, data["shortcut"])
    nuke.menu("Node Graph").addCommand("Snap Backdrop", wrapped(snap), data["snap"])
    panels.registerWidgetAsPanel(
        "BackdropManager.panel.BackdropPanel",
        "Backdrop Manager",
        "BackdropManager.BackdropPanel",
    )
    nuke.BackdropManagerPanel = BackdropPanel
    _REGISTERED = True