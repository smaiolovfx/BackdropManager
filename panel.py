"""Dockable BackdropManager panel."""

from functools import partial

import nuke

from .colors import interface_to_rgb, rgb_to_hex, rgb_to_interface
from .dag import wrapped
from .backdrop_dialog import NUKE_VERSION_MAJOR
from .dialog_launchers import gui, guiEdit, guiUI
from .operations import snap
from .paths import icon_path
from .qt import QtGui, QtWidgets
from .settings import Overrides
from .widgets import DragButton


class BackdropPanel(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setAcceptDrops(True)
        self.settings = Overrides()
        self.d = self.settings.restore()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self._build_toolbar()
        self.makeBoxes()

    def _build_toolbar(self):
        gbox = QtWidgets.QHBoxLayout()
        gbox.setContentsMargins(30, 0, 30, 0)
        gbox.setSpacing(5)
        self.layout.addLayout(gbox)

        button_data = [
            ("Backdrop.png", "Make backdrop", guiUI),
            ("Edit.png", "Edit selected backdrops", guiEdit),
            ("Toggle.png", "Toggle fill/border mode on selected backdrops", wrapped(self.toggle)),
            ("Selected.png", "Set selected backdrops to default style", wrapped(self.setStyleSel)),
            ("All.png", "Set all backdrops to default style", wrapped(self.setStyle)),
            ("Snap.png", "Snap backdrop size", wrapped(snap)),
            ("Settings.png", "Open settings", gui),
        ]

        for icon, tooltip, callback in button_data:
            btn = QtWidgets.QPushButton()
            btn.setIcon(QtGui.QIcon(icon_path(icon)))
            btn.setToolTip(tooltip)
            btn.setFixedSize(40, 25)
            btn.clicked.connect(callback)
            gbox.addWidget(btn)

    def get_data(self):
        self.settings = Overrides()
        data = self.settings.restore()
        self.colors = []
        self.labels = []
        for index in range(self.box_layout.count()):
            widget = self.box_layout.itemAt(index).widget()
            if widget is None or not hasattr(widget, "data"):
                continue
            self.colors.append(widget.data)
            self.labels.append(getattr(widget, "label", ""))
        data["colors"] = self.colors
        data["labels"] = self.labels
        self.settings.save()

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        pos = event.pos()
        widget = event.source()
        if widget is None:
            event.ignore()
            return

        for index in range(self.box_layout.count()):
            item = self.box_layout.itemAt(index).widget()
            drop_here = pos.x() <= item.x() + item.size().width() // 2
            if drop_here:
                self.box_layout.insertWidget(index, widget)
                self.get_data()
                break
        else:
            self.box_layout.addWidget(widget)
            self.get_data()

        event.accept()

    def setStyleSel(self):
        self.d = self.settings.restore()
        alignment = "<" + self.d["align"] + ">"
        bold = "<b>" if self.d["bold"] is True else ""
        italic = "<i>" if self.d["italic"] is True else ""

        for node in nuke.selectedNodes():
            node.setSelected(False)
            if node.Class() == "BackdropNode":
                node.setSelected(True)

        for node in nuke.selectedNodes():
            label = node["label"].value().split(">")[-1]
            node.knob("label").setValue(alignment + bold + italic + label)
            node.knob("note_font").setValue(self.d["font"])
            node.knob("note_font_size").setValue(self.d["font_size"])
            if NUKE_VERSION_MAJOR >= 12:
                node.knob("appearance").setValue(self.d["style"])
            node.knob("border_width").setValue(self.d["width"])
            node.knob("bookmark").setValue(self.d["bookmark"])

    def setStyle(self):
        self.d = self.settings.restore()
        alignment = "<" + self.d["align"] + ">"
        bold = "<b>" if self.d["bold"] is True else ""
        italic = "<i>" if self.d["italic"] is True else ""

        for node in nuke.allNodes():
            if node.Class() == "BackdropNode":
                label = node["label"].value().split(">")[-1]
                node.knob("label").setValue(alignment + bold + italic + label)
                node.knob("note_font").setValue(self.d["font"])
                node.knob("note_font_size").setValue(self.d["font_size"])
                if NUKE_VERSION_MAJOR >= 12:
                    node.knob("appearance").setValue(self.d["style"])
                node.knob("border_width").setValue(self.d["width"])
                node.knob("bookmark").setValue(self.d["bookmark"])

    def makeBoxes(self):
        self.box_group = QtWidgets.QGroupBox()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(5)
        self.box_layout = QtWidgets.QHBoxLayout()
        self.box_layout.setSpacing(15)
        vbox.addLayout(self.box_layout)
        self.box_group.setLayout(vbox)
        self.layout.addWidget(self.box_group)

        self.settings = Overrides()
        data = self.settings.restore()
        self.colors = data["colors"]
        self.labels = data.setdefault("labels", [])
        while len(self.labels) < len(self.colors):
            self.labels.append("")

        for index, color in enumerate(self.colors):
            self._add_color_button(color, self.labels[index])

        self.box = QtWidgets.QHBoxLayout()
        self.box.setContentsMargins(0, 10, 0, 0)
        self.box.setSpacing(10)
        self.box.addStretch(375)
        self.layout.addLayout(self.box)

        minb = QtWidgets.QPushButton("-")
        minb.setToolTip("Remove last color.")
        minb.setFixedSize(20, 20)
        minb.clicked.connect(self.min)
        self.box.addWidget(minb)

        addb = QtWidgets.QPushButton("+")
        addb.setToolTip("Add a new color.")
        addb.clicked.connect(self.add)
        addb.setFixedSize(20, 20)
        self.box.addWidget(addb)

        refresh = QtWidgets.QPushButton("Reload")
        refresh.setToolTip("Refresh color boxes")
        refresh.setFixedSize(60, 20)
        refresh.clicked.connect(self.clear)
        self.box.addWidget(refresh)

    def min(self):
        if not self.colors:
            return
        self.colors.pop(-1)
        if self.labels:
            self.labels.pop(-1)
        self.settings.save()
        self.clear()

    def add(self):
        col = nuke.getColor()
        if col:
            col = interface_to_rgb(col)
            self.colors.append(col)
            self.labels.append("")
            self.settings.save()
            self._add_color_button(col, "")

    def _add_color_button(self, color, label):
        btn = DragButton()
        btn.setToolTip("Recolor selected backdrops and sticky notes")
        btn.setStyleSheet("background-color: %s;" % rgb_to_hex(color))
        btn.set_data(color)
        btn.label = label
        btn.setFixedSize(20, 20)
        self.box_layout.addWidget(btn)
        btn.clicked.connect(partial(wrapped(self.setColor), btn))

    def clear(self):
        self.box_group.deleteLater()
        self.box.deleteLater()
        self.makeBoxes()

    def setColor(self, color_source, *args):
        if isinstance(color_source, int):
            color_value = self.colors[color_source]
        else:
            color_value = color_source.data
        color = rgb_to_interface(color_value)

        for node in nuke.selectedNodes():
            node.setSelected(False)
            if node.Class() == "StickyNote" or node.Class() == "BackdropNode":
                node.setSelected(True)

        for node in nuke.selectedNodes():
            node.knob("tile_color").setValue(color)

    def toggle(self):
        if NUKE_VERSION_MAJOR < 12:
            return

        for node in nuke.selectedNodes():
            node.setSelected(False)
            if node.Class() == "BackdropNode":
                node.setSelected(True)

        for node in nuke.selectedNodes():
            if node["appearance"].value() == "Fill":
                node.knob("appearance").setValue("Border")
            else:
                node.knob("appearance").setValue("Fill")