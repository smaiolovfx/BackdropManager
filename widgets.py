"""Reusable Qt widgets used by BackdropManager dialogs."""

from .qt import Qt, QtCore, QtGui, QtWidgets


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
    """Replacement for setCurrentText that works in Nuke 10."""
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
            drag.exec_(Qt.MoveAction)


class KeySequenceWidget(QtWidgets.QWidget):
    keySequenceChanged = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setMinimumWidth(140)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        self.button = KeySequenceButton(self)
        self.button.setFixedWidth(100)
        self.clearButton = QtWidgets.QPushButton(self, iconSize=QtCore.QSize(16, 16))
        self.clearButton.setText("Clear")
        self.clearButton.setFixedWidth(50)

        layout.addWidget(self.button)
        layout.addWidget(self.clearButton)

        self.clearButton.clicked.connect(self.clear)
        self.button.setToolTip(
            "Sets the key sequence used to make a backdrops. Click to start recording."
        )
        self.clearButton.setToolTip("Clear the key sequence.")

    def setShortcut(self, shortcut):
        self.button.setKeySequence(shortcut)

    def shortcut(self):
        return self.button.keySequence()

    def clear(self):
        if self.button.isRecording():
            self.button.cancelRecording()
        if not self.button.keySequence().isEmpty():
            self.button.setKeySequence(QtGui.QKeySequence())
        self.keySequenceChanged.emit()

    def setModifierlessAllowed(self, allow):
        self.button._modifierlessAllowed = allow

    def isModifierlessAllowed(self):
        return self.button._modifierlessAllowed


class KeySequenceButton(QtWidgets.QPushButton):
    MAX_NUM_KEYSTROKES = 1

    def __init__(self, parent=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self._modifierlessAllowed = True
        self._seq = QtGui.QKeySequence()
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._isrecording = False
        self.clicked.connect(self.startRecording)
        self._timer.timeout.connect(self.doneRecording)

    def setKeySequence(self, seq):
        self._seq = seq
        self.updateDisplay()

    def keySequence(self):
        if self._isrecording:
            self.doneRecording()
        return self._seq

    def updateDisplay(self):
        if self._isrecording:
            text = self._recseq.toString(QtGui.QKeySequence.NativeText).replace("&", "&&")
            if self._modifiers:
                if text:
                    text += ","
                text += QtGui.QKeySequence(self._modifiers).toString(
                    QtGui.QKeySequence.NativeText
                )
            elif self._recseq.isEmpty():
                text = "Input"
            text += " ..."
        else:
            text = self._seq.toString(QtGui.QKeySequence.NativeText).replace("&", "&&")
        self.setText(text)

    def isRecording(self):
        return self._isrecording

    def event(self, event):
        if self._isrecording:
            if event.type() == QtCore.QEvent.KeyPress:
                self.keyPressEvent(event)
                return True
        return QtWidgets.QPushButton.event(self, event)

    def keyPressEvent(self, event):
        if not self._isrecording:
            return QtWidgets.QPushButton.keyPressEvent(self, event)
        if event.isAutoRepeat():
            return

        modifiers = event.modifiers()
        event.accept()

        all_modifiers = (
            -1,
            Qt.Key_Shift,
            Qt.Key_Control,
            Qt.Key_AltGr,
            Qt.Key_Alt,
            Qt.Key_Meta,
            Qt.Key_Menu,
        )
        key = event.key()

        if (
            key not in all_modifiers
            and (
                self._modifierlessAllowed
                or self._recseq.count() > 0
                or modifiers & ~Qt.SHIFT
                or not event.text()
                or (
                    modifiers & Qt.SHIFT
                    and key
                    in (
                        Qt.Key_Return,
                        Qt.Key_Space,
                        Qt.Key_Tab,
                        Qt.Key_Backtab,
                        Qt.Key_Backspace,
                        Qt.Key_Delete,
                        Qt.Key_Escape,
                    )
                )
            )
        ):
            if key == Qt.Key_Backtab and modifiers & Qt.SHIFT:
                key = Qt.Key_Tab | modifiers
            elif Qt.Key_Exclam <= key <= Qt.Key_At or Qt.Key_Z < key <= 0x0FF:
                key = key | (modifiers & ~int(Qt.SHIFT))
            else:
                key = key | modifiers

            if self._recseq.count() < self.MAX_NUM_KEYSTROKES:
                keys = list(self._recseq)
                keys.append(key)
                self._recseq = QtGui.QKeySequence(*keys)

        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def keyReleaseEvent(self, event):
        if not self._isrecording:
            return QtWidgets.QPushButton.keyReleaseEvent(self, event)
        modifiers = int(event.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
        event.accept()
        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def hideEvent(self, event):
        if self._isrecording:
            self.cancelRecording()
        QtWidgets.QPushButton.hideEvent(self, event)

    def controlTimer(self):
        if self._modifiers or self._recseq.isEmpty():
            self._timer.stop()
        else:
            self._timer.start(600)

    def startRecording(self):
        self.setDown(True)
        self.setStyleSheet("text-align: left;")
        self._isrecording = True
        self._recseq = QtGui.QKeySequence()
        self._modifiers = int(
            QtWidgets.QApplication.keyboardModifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META)
        )
        self.grabKeyboard()
        self.updateDisplay()

    def doneRecording(self):
        self._seq = self._recseq
        self.cancelRecording()
        self.clearFocus()
        self.parentWidget().keySequenceChanged.emit()

    def cancelRecording(self):
        if not self._isrecording:
            return
        self.setDown(False)
        self.setStyleSheet("")
        self._isrecording = False
        self.releaseKeyboard()
        self.updateDisplay()