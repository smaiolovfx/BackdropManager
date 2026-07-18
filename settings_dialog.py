"""Settings dialog for BackdropManager."""

from functools import partial

import nuke

from .colors import interface_to_rgb, rgb_to_hex, rgb_to_interface
from .qt import Qt, QtCore, QtGui, QtWidgets
from .settings import Overrides
from .widgets import DragButton, KeySequenceWidget, set_current_text, widget_with_label

NUKE_VERSION_MAJOR = nuke.NUKE_VERSION_MAJOR


class BackdropManagerSettings(QtWidgets.QDialog):
    closed = QtCore.Signal()

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setAcceptDrops(True)

        self.settings = Overrides()
        data = self.settings.restore()
        self.data = data

        self.setWindowTitle("Backdrop Manager Settings")
        self.setMinimumSize(470, 700)
        self.setWhatsThis(
            "This sets the default values for backdrop settings. Values can be changed "
            "when making a backdrop. Add or change color boxes to set presets for "
            "backdrop colors."
        )

        try:
            self.move(data["xpos"], data["ypos"])
        except Exception:
            pass

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        set_group = QtWidgets.QGroupBox("Settings")
        set_layout = QtWidgets.QVBoxLayout()
        set_layout.setSpacing(10)
        set_layout.setContentsMargins(10, 10, 10, 10)
        set_group.setLayout(set_layout)
        self.layout.addWidget(set_group, 1)

        self._build_shortcut_controls(set_layout, data)
        self._build_font_controls(set_layout, data)
        self._build_style_controls(set_layout, data)
        self._build_color_presets(data)
        self._build_footer_buttons()

    def _build_shortcut_controls(self, set_layout, data):
        box = QtWidgets.QHBoxLayout()
        box.setContentsMargins(20, 0, 0, 0)
        box.setSpacing(0)
        set_layout.addLayout(box)

        self.shortcut_widget = KeySequenceWidget()
        self.shortcut_widget.setShortcut(QtGui.QKeySequence(data["shortcut"]))
        box.addWidget(widget_with_label(self.shortcut_widget, "Shortcut"))
        box.addStretch(1)

        box7 = QtWidgets.QHBoxLayout()
        box7.setContentsMargins(40, 0, 0, 0)
        box7.setSpacing(10)
        set_layout.addLayout(box7)

        self.snap_widget = KeySequenceWidget()
        self.snap_widget.setShortcut(QtGui.QKeySequence(data["snap"]))
        box7.addWidget(widget_with_label(self.snap_widget, "Snap"))

        self.psize = QtWidgets.QSpinBox(self)
        self.psize.setToolTip("Set default snap padding size.")
        self.psize.setFixedSize(80, 24)
        self.psize.setRange(0, 999)
        self.psize.setValue(data["padding"])
        box7.addWidget(widget_with_label(self.psize, "padding"))
        box7.addStretch(1)

    def _build_font_controls(self, set_layout, data):
        box2 = QtWidgets.QHBoxLayout()
        box2.setContentsMargins(45, 0, 0, 0)
        box2.setSpacing(5)
        set_layout.addLayout(box2)
        box2.addWidget(QtWidgets.QLabel("font"))

        self.font = QtWidgets.QFontComboBox()
        self.font.setToolTip("Set default label font.")
        set_current_text(self.font, data["font"])
        box2.addWidget(self.font)

        self.fsize = QtWidgets.QSpinBox(self)
        self.fsize.setToolTip("Set default label font size.")
        self.fsize.setFixedSize(80, 24)
        self.fsize.setRange(0, 999)
        self.fsize.setValue(data["font_size"])
        box2.addWidget(self.fsize)

        self.boldv = data["bold"]
        self.boldb = QtWidgets.QPushButton("B")
        self.boldb.setStyleSheet("font: bold;")
        self.boldb.setToolTip("Make label font bold by default.")
        self.boldb.setFixedSize(20, 20)
        if self.boldv is True:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
        self.boldb.clicked.connect(self.bold)
        box2.addWidget(self.boldb)

        self.italicv = data["italic"]
        self.italicb = QtWidgets.QPushButton("I")
        self.italicb.setStyleSheet("font: italic;")
        self.italicb.setToolTip("Make label font italic by default.")
        self.italicb.setFixedSize(20, 20)
        if self.italicv is True:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
        self.italicb.clicked.connect(self.italic)
        box2.addWidget(self.italicb)
        box2.addStretch(1)

        box3 = QtWidgets.QHBoxLayout()
        box3.setContentsMargins(10, 0, 0, 0)
        box3.setSpacing(0)
        set_layout.addLayout(box3)

        self.format = QtWidgets.QComboBox()
        self.format.addItem("left")
        self.format.addItem("center")
        self.format.setToolTip("Set default label text alignment.")
        set_current_text(self.format, data["align"])
        box3.addWidget(widget_with_label(self.format, "label align"))
        box3.addStretch(1)

    def _build_style_controls(self, set_layout, data):
        if NUKE_VERSION_MAJOR >= 12:
            box4 = QtWidgets.QHBoxLayout()
            box4.setContentsMargins(0, 0, 0, 0)
            box4.setSpacing(5)
            set_layout.addLayout(box4)
            box4.addWidget(QtWidgets.QLabel("appearance"))

            self.style_drop = QtWidgets.QComboBox()
            self.style_drop.addItem("Fill")
            self.style_drop.addItem("Border")
            self.style_drop.setToolTip("Set default style.")
            set_current_text(self.style_drop, data["style"])
            box4.addWidget(self.style_drop)

            self.w = QtWidgets.QSpinBox()
            self.w.setToolTip("Set default border width value.")
            self.w.setFixedSize(80, 24)
            self.w.setValue(data["width"])
            box4.addWidget(widget_with_label(self.w, "width"))
            box4.addStretch(1)

        box5 = QtWidgets.QHBoxLayout()
        box5.setContentsMargins(73, 0, 0, 0)
        box5.setSpacing(0)
        set_layout.addLayout(box5)

        self.bm = QtWidgets.QCheckBox("bookmark")
        self.bm.setToolTip("Set default bookmark value.")
        self.bm.setChecked(data["bookmark"])
        box5.addWidget(self.bm)

        box6 = QtWidgets.QHBoxLayout()
        box6.setContentsMargins(23, 0, 260, 0)
        box6.setSpacing(0)
        set_layout.addLayout(box6)

        self.zorder = QtWidgets.QSpinBox(self)
        self.zorder.setToolTip("Set default Z order value.")
        self.zorder.setFixedSize(80, 24)
        self.zorder.setRange(-999, 999)
        self.zorder.setValue(data["zorder"])
        box6.addWidget(widget_with_label(self.zorder, "Z Order"))
        box6.addStretch(1)

    def _build_color_presets(self, data):
        box_group = QtWidgets.QGroupBox("Color Presets")
        box_group.setContentsMargins(0, 25, 0, 0)
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(15)
        self.box_layout = QtWidgets.QGridLayout()
        self.box_layout.setSpacing(15)
        vbox.addLayout(self.box_layout)
        box_group.setLayout(vbox)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(box_group)
        self.layout.addWidget(self.scroll, 2)

        self.colors = data["colors"]
        self.labels = data.setdefault("labels", [])
        while len(self.labels) < len(self.colors):
            self.labels.append("")
        self.row = 0
        self.boxes = []
        self.titles = []

        for index, color in enumerate(self.colors):
            self._add_color_preset_row(index, color, self.labels[index])

        pmbox = QtWidgets.QHBoxLayout()
        pmbox.setContentsMargins(0, 0, 0, 0)
        pmbox.setSpacing(10)
        pmbox.addStretch(375)
        vbox.addLayout(pmbox)

        prefs = nuke.toNode("preferences")
        pcol = rgb_to_hex(interface_to_rgb(prefs["UIBackColor"].value()))

        minb = QtWidgets.QPushButton("-")
        minb.setToolTip("Remove last color box.")
        minb.setStyleSheet("background-color: %s;" % pcol)
        minb.setFixedSize(20, 20)
        minb.clicked.connect(self.min)
        pmbox.addWidget(minb)

        addb = QtWidgets.QPushButton("+")
        addb.setToolTip("Add a new color box.")
        addb.setStyleSheet("background-color: %s;" % pcol)
        addb.clicked.connect(self.add)
        addb.setFixedSize(20, 20)
        pmbox.addWidget(addb)

    def _add_color_preset_row(self, index, color, label):
        btn = DragButton()
        self.boxes.append(btn)
        btn.setToolTip("Click to change color.")
        btn.setAutoFillBackground(True)
        palette = btn.palette()
        palette.setColor(btn.backgroundRole(), QtGui.QColor(rgb_to_hex(color)))
        btn.setPalette(palette)
        btn.set_data(color)
        btn.setFixedSize(20, 20)

        title = QtWidgets.QLineEdit()
        self.titles.append(title)
        title.setToolTip("Enter default label.")
        title.setText(label)

        self.row += 1
        self.box_layout.addWidget(btn, self.row - 1, 0)
        self.box_layout.addWidget(title, self.row - 1, 1)
        btn.clicked.connect(partial(self.btnClicked, index, btn))

    def _build_footer_buttons(self):
        box7 = QtWidgets.QHBoxLayout()
        box7.setSpacing(60)
        self.layout.addLayout(box7)

        self.button_default = QtWidgets.QPushButton("Set to default")
        self.button_default.setToolTip("Set ALL values back to default, including colors.")
        self.button_default.clicked.connect(self.default)
        box7.addWidget(self.button_default)

        self.button_close = QtWidgets.QPushButton("Save")
        self.button_close.setToolTip("Save settings.")
        self.button_close.clicked.connect(self.closeSave)
        box7.addWidget(self.button_close)
        self.button_close.setFocus()

        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_cancel.setToolTip("Close window and revert back to previous saved settings.")
        self.button_cancel.clicked.connect(self.close)
        box7.addWidget(self.button_cancel)

    def min(self):
        if not self.boxes:
            return
        for widgets in [self.boxes, self.titles]:
            self.box_layout.removeWidget(widgets[-1])
            widgets[-1].deleteLater()
            widgets[-1] = None
            widgets.pop(-1)
        self.colors.pop(-1)
        try:
            self.labels.pop(-1)
        except Exception:
            pass
        self.row -= 1
        self.box_layout.update()

    def add(self):
        col = nuke.getColor()
        if col:
            col = interface_to_rgb(col)
            self.colors.append(col)
            self.labels.append("")
            self._add_color_preset_row(len(self.boxes), col, "")
            self.box_layout.update()

    def bold(self):
        if self.boldv is False:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
            self.boldv = True
        else:
            self.boldb.setStyleSheet("font: bold; background-color: ;")
            self.boldv = False

    def italic(self):
        if self.italicv is False:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
            self.italicv = True
        else:
            self.italicb.setStyleSheet("font: italic; background-color: ;")
            self.italicv = False

    def btnClicked(self, color_idx, btn, *args):
        color = self.colors[color_idx]
        color = rgb_to_interface(color)
        col = nuke.getColor(color)
        if not col:
            return
        col = interface_to_rgb(col)
        self.colors[color_idx] = col
        btn.setStyleSheet("background-color: %s;" % rgb_to_hex(col))

    def default(self):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setText("Clear all settings?")
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setStandardButtons(QtWidgets.QMessageBox.Reset | QtWidgets.QMessageBox.Cancel)
        message_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        if message_box.exec_() == QtWidgets.QMessageBox.Reset:
            self.settings.clear()
            self.close()
            from .dialog_launchers import gui

            gui()

    def closeSave(self, evt=None):
        settings = self.data
        settings["shortcut"] = self.shortcut_widget.shortcut().toString()
        settings["snap"] = self.snap_widget.shortcut().toString()
        settings["padding"] = self.psize.value()
        settings["font"] = self.font.currentText()
        settings["font_size"] = self.fsize.value()
        settings["bold"] = self.boldv
        settings["italic"] = self.italicv
        settings["align"] = self.format.currentText()
        settings["bookmark"] = self.bm.isChecked()
        settings["zorder"] = self.zorder.value()
        settings["xpos"] = self.pos().x()
        settings["ypos"] = self.pos().y()
        settings["colors"] = self.colors
        settings["labels"] = [widget.text() for widget in self.titles]

        if NUKE_VERSION_MAJOR >= 12:
            settings["style"] = self.style_drop.currentText()
            settings["width"] = self.w.value()

        self.settings.defaults = settings
        self.settings.save()
        self.close()
        self.closed.emit()

    def closeEvent(self, event):
        self.closed.emit()
        QtWidgets.QWidget.closeEvent(self, event)