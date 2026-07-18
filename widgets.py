"""Reusable Qt widgets used by BackdropManager dialogs."""

from .qt import Qt, QtCore, QtGui, QtWidgets, qt_exec


def widget_with_label(towrap, text):
    """Wrap a widget in a layout with a label to the left."""
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(5)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(QtWidgets.QLabel(text))
    layout.addWidget(towrap)
    widget.setLayout(layout)
    return widget


def set_current_text(widget, text):
    """Select a combo item by text (no-op if the text is not present)."""
    index = widget.findText(text, QtCore.Qt.MatchFixedString)
    if index >= 0:
        widget.setCurrentIndex(index)


class DragButton(QtWidgets.QPushButton):
    def set_data(self, data):
        self.data = data

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MiddleButton:
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            drag.setMimeData(mime)

            pixmap = QtGui.QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            qt_exec(drag, Qt.MoveAction)


class KeySequenceWidget(QtWidgets.QWidget):
    """Shortcut editor backed by Qt's QKeySequenceEdit (correct live display)."""

    keySequenceChanged = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setMinimumWidth(140)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        self.edit = QtWidgets.QKeySequenceEdit(self)
        if hasattr(self.edit, "setMaximumSequenceLength"):
            self.edit.setMaximumSequenceLength(1)
        self.clearButton = QtWidgets.QPushButton(self)
        self.clearButton.setText("Clear")
        self.clearButton.setFixedWidth(50)

        layout.addWidget(self.edit)
        layout.addWidget(self.clearButton)

        self.clearButton.clicked.connect(self.clear)
        self.edit.editingFinished.connect(self._truncate)
        self.edit.keySequenceChanged.connect(lambda *_: self.keySequenceChanged.emit())
        self.edit.setToolTip(
            "Sets the key sequence used to make a backdrop. Click and type a shortcut."
        )
        self.clearButton.setToolTip("Clear the key sequence.")

    def setShortcut(self, shortcut):
        self.edit.setKeySequence(shortcut)

    def shortcut(self):
        return self._first_chord(self.edit.keySequence())

    def clear(self, *args):
        self.edit.clear()
        self.keySequenceChanged.emit()

    def _truncate(self):
        current = self.edit.keySequence()
        if current.isEmpty() or current.count() <= 1:
            return
        self.edit.setKeySequence(self._first_chord(current))

    @staticmethod
    def _first_chord(seq):
        if seq.isEmpty():
            return seq
        return QtGui.QKeySequence(seq[0])
