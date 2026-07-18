"""Singleton dialog launchers used by menus and panels."""

import nuke

from .backdrop_dialog import BackdropManagerUI
from .settings_dialog import BackdropManagerSettings

_dialogs = {"settings": None, "backdrop": None, "edit": None}


def _show_or_raise(key, factory, prepare=None):
    """Show an existing dialog, or create one."""
    existing = _dialogs[key]
    if existing is not None:
        existing.show()
        existing.activateWindow()
        existing.raise_()
        return existing

    dialog = factory()
    if prepare is not None:
        prepare(dialog)

    def _clear():
        _dialogs[key] = None

    dialog.closed.connect(_clear)
    _dialogs[key] = dialog
    dialog.show()
    return dialog


def gui(*args):
    dialog = _show_or_raise("settings", BackdropManagerSettings)
    dialog.setFocus()


def guiUI(*args):
    _show_or_raise("backdrop", BackdropManagerUI)


def guiEdit(*args):
    for node in nuke.selectedNodes():
        node.setSelected(False)
        if node.Class() == "BackdropNode":
            node.setSelected(True)

    if len(nuke.selectedNodes()) < 1:
        nuke.message("Select one or more Backdrop nodes to edit.")
        return

    _show_or_raise("edit", BackdropManagerUI, prepare=lambda d: d.switch())
