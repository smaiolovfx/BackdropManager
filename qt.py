"""Qt compatibility imports for supported Nuke versions."""

try:
    from Qt import QtCore, QtGui, QtWidgets
    from Qt.QtCore import Qt
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Qt
    except ImportError:
        from PySide import QtCore, QtGui
        from PySide import QtGui as QtWidgets
        from PySide.QtCore import Qt