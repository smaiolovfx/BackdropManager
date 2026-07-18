"""Qt compatibility imports for Nuke 11+ (PySide2 / PySide6)."""

try:
    from Qt import QtCore, QtGui, QtWidgets
    from Qt.QtCore import Qt
except ImportError:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import Qt
    except ImportError:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Qt


def qt_exec(widget, *args):
    """Call ``exec()`` / ``exec_()`` across PySide2 and PySide6."""
    return (getattr(widget, "exec", None) or widget.exec_)(*args)
