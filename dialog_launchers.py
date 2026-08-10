"""Singleton dialog launchers used by menus and panels."""

import nuke

from .backdrop_dialog import BackdropManagerUI
from .dag import current_dag, in_dag, remember_dag
from .settings_dialog import BackdropManagerSettings

_dialogs = {"settings": None, "backdrop": None, "edit": None}


def _show_or_raise(key, factory, prepare=None):
    """Show an existing dialog, or create one."""
    existing = _dialogs[key]
    if existing is not None:
        if prepare is not None:
            prepare(existing)
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


def current_settings_dialog():
    """Return the open settings dialog, or None."""
    return _dialogs["settings"]


def gui(*args):
    dialog = _show_or_raise("settings", BackdropManagerSettings)
    dialog.setFocus()


def guiUI(*args):
    ctx = current_dag()
    remember_dag(ctx)

    def prepare(dialog):
        dialog.set_dag_context(ctx)
        dialog.reset_to_create()

    _show_or_raise("backdrop", BackdropManagerUI, prepare=prepare)


def guiEdit(*args):
    ctx = current_dag()
    remember_dag(ctx)
    with in_dag(ctx):
        for node in nuke.selectedNodes():
            node.setSelected(False)
            if node.Class() == "BackdropNode":
                node.setSelected(True)

        if len(nuke.selectedNodes()) < 1:
            nuke.message("Select one or more Backdrop nodes to edit.")
            return

    def prepare(dialog):
        dialog.set_dag_context(ctx)
        dialog.switch()

    _show_or_raise("edit", BackdropManagerUI, prepare=prepare)
