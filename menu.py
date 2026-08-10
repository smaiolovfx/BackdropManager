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

    if nuke.NUKE_VERSION_MAJOR < 11:
        nuke.tprint("BackdropManager requires Nuke 11 or later.")
        _REGISTERED = True
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
    _register_node_graph_commands(data)
    panels.registerWidgetAsPanel(
        "BackdropManager.panel.BackdropPanel",
        "Backdrop Manager",
        "BackdropManager.BackdropPanel",
    )
    nuke.BackdropManagerPanel = BackdropPanel
    _REGISTERED = True


def apply_shortcuts(data):
    """Re-bind Node Graph shortcuts from settings (e.g. after Save)."""
    if not nuke.env["gui"]:
        return
    _register_node_graph_commands(data)


def _register_node_graph_commands(data):
    """Add or replace Create/Snap commands (window context — matches original)."""
    # ponytail: no shortcutContext=2 — DAG context on the Node Graph menu
    # made hotkeys dead; window default is what worked historically.
    node_graph = nuke.menu("Node Graph")
    entries = (
        ("Create Backdrop", data.get("shortcut") or "", guiUI),
        ("Snap Backdrop", data.get("snap") or "", wrapped(snap)),
    )
    for name, shortcut, command in entries:
        if node_graph.findItem(name) is not None:
            node_graph.removeItem(name)
        node_graph.addCommand(name, command, shortcut)
