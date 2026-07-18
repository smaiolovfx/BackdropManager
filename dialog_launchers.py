"""Singleton dialog launchers used by menus and panels."""

import nuke

from .backdrop_dialog import BackdropManagerUI
from .settings import load_settings
from .settings_dialog import BackdropManagerSettings

_settings_dialog = None
_backdrop_dialog = None
_edit_dialog = None


def _on_settings_closed():
    global _settings_dialog
    _settings_dialog = None


def _on_backdrop_closed():
    global _backdrop_dialog
    _backdrop_dialog = None


def _on_edit_closed():
    global _edit_dialog
    _edit_dialog = None


def gui(*args):
    global _settings_dialog
    load_settings()

    if _settings_dialog is not None:
        _settings_dialog.show()
        _settings_dialog.setFocus()
        _settings_dialog.activateWindow()
        _settings_dialog.raise_()
        return

    _settings_dialog = BackdropManagerSettings()
    _settings_dialog.closed.connect(_on_settings_closed)
    _settings_dialog.show()


def guiUI(*args):
    global _backdrop_dialog
    load_settings()

    if _backdrop_dialog is not None:
        _backdrop_dialog.show()
        _backdrop_dialog.activateWindow()
        _backdrop_dialog.raise_()
        return

    _backdrop_dialog = BackdropManagerUI()
    _backdrop_dialog.closed.connect(_on_backdrop_closed)
    _backdrop_dialog.show()


def guiEdit(*args):
    global _edit_dialog
    load_settings()

    if _edit_dialog is not None:
        _edit_dialog.show()
        _edit_dialog.activateWindow()
        _edit_dialog.raise_()
        return

    for node in nuke.selectedNodes():
        node.setSelected(False)
        if node.Class() == "BackdropNode":
            node.setSelected(True)

    if len(nuke.selectedNodes()) >= 1:
        _edit_dialog = BackdropManagerUI()
        _edit_dialog.switch()
        _edit_dialog.closed.connect(_on_edit_closed)
        _edit_dialog.show()
    else:
        nuke.message("Select one or more Backdrop nodes to edit.")
