"""Create and edit backdrop dialog."""

import traceback

import nuke

from .colors import hex_to_interface, interface_to_rgb, rgb_to_hex, rgb_to_interface
from .dag import active_dag_node, wrapped
from .qt import QtCore, QtGui, QtWidgets
from .settings import Overrides
from .widgets import set_current_text, widget_with_label

NUKE_VERSION_MAJOR = nuke.NUKE_VERSION_MAJOR


class BackdropManagerUI(QtWidgets.QDialog):
    closed = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        overrides = Overrides()
        self.data = overrides.restore()

        self.setWindowTitle("Make backdrop")
        self.setMinimumSize(450, 300)
        self.setFocus()
        self._editing = False

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(25)
        self.setLayout(layout)

        set_group = QtWidgets.QGroupBox("Backdrop")
        set_layout = QtWidgets.QVBoxLayout()
        set_layout.setSpacing(10)
        set_group.setLayout(set_layout)
        layout.addWidget(set_group)

        self._build_color_controls(set_layout, overrides)
        self._build_label_controls(set_layout)
        self._build_font_controls(set_layout)
        self._build_style_controls(set_layout)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok
        )
        layout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(wrapped(self.makeBackdrop))
        self.buttonBox.rejected.connect(self.close)
        self.label.setFocus()

    def _build_color_controls(self, set_layout, overrides):
        box = QtWidgets.QHBoxLayout()
        box.setContentsMargins(40, 0, 0, 0)
        box.setSpacing(0)
        set_layout.addLayout(box)

        self.colBox = QtWidgets.QComboBox()
        self.colBox.setFixedSize(100, 25)
        self.colors = self.data["colors"]
        try:
            self.labels = self.data["labels"]
        except Exception:
            self.labels = []
            for color in self.colors:
                self.labels.append("")
            self.data["labels"] = self.labels
            overrides.save()

        try:
            base_col = rgb_to_hex(self.colors[0])
        except Exception:
            base_col = None

        self.colBox.setAutoFillBackground(True)
        palette = self.colBox.palette()
        palette.setColor(self.colBox.backgroundRole(), QtGui.QColor(base_col))
        self.colBox.setPalette(palette)

        model = self.colBox.model()
        for row, (color, label) in enumerate(zip(self.colors, self.labels)):
            self.colBox.addItem(label)
            model.setData(model.index(row, 0), QtGui.QColor(rgb_to_hex(color)), QtCore.Qt.BackgroundRole)

        box.addWidget(widget_with_label(self.colBox, "color"))
        self.colBox.activated.connect(self.changeColor)
        box.addStretch(1)

    def _build_label_controls(self, set_layout):
        self.box6 = QtWidgets.QHBoxLayout()
        self.box6.setContentsMargins(40, 0, 0, 0)
        self.box6.setSpacing(10)
        set_layout.addLayout(self.box6)

        self.labelt = QtWidgets.QCheckBox()
        self.labelt.setChecked(1)
        self.labelt.setVisible(False)
        self.labelt.setStyleSheet("background-color: #595959;")
        self.labelt.stateChanged.connect(self.enableL)
        self.box6.addWidget(self.labelt)

        self.label = QtWidgets.QLineEdit()
        self.label.setFixedWidth(200)
        self.label.setText("")
        self.box6.addWidget(widget_with_label(self.label, "label"))

        self.format = QtWidgets.QComboBox()
        self.format.addItem("left")
        self.format.addItem("center")
        set_current_text(self.format, self.data["align"])
        self.box6.addWidget(widget_with_label(self.format, "align"))
        self.box6.addStretch(1)

    def _build_font_controls(self, set_layout):
        box2 = QtWidgets.QHBoxLayout()
        box2.setContentsMargins(45, 0, 0, 0)
        box2.setSpacing(0)
        set_layout.addLayout(box2)

        self.font = QtWidgets.QFontComboBox()
        set_current_text(self.font, self.data["font"])
        box2.addWidget(widget_with_label(self.font, "font"))

        self.fsize = QtWidgets.QSpinBox(self)
        self.fsize.setFixedSize(80, 25)
        self.fsize.setRange(0, 999)
        self.fsize.setValue(self.data["font_size"])
        box2.addWidget(self.fsize)

        self.boldv = self.data["bold"]
        self.boldb = QtWidgets.QPushButton("B")
        self.boldb.setStyleSheet("font: bold;")
        self.boldb.setFixedSize(20, 20)
        if self.boldv is True:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
        self.boldb.clicked.connect(self.boldT)
        box2.addWidget(self.boldb)

        self.italicv = self.data["italic"]
        self.italicb = QtWidgets.QPushButton("I")
        self.italicb.setStyleSheet("font: italic;")
        self.italicb.setFixedSize(20, 20)
        if self.italicv is True:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
        self.italicb.clicked.connect(self.italicT)
        box2.addWidget(self.italicb)
        box2.addStretch(1)

    def _build_style_controls(self, set_layout):
        if NUKE_VERSION_MAJOR >= 12:
            box3 = QtWidgets.QHBoxLayout()
            box3.setContentsMargins(0, 0, 0, 0)
            box3.setSpacing(10)
            set_layout.addLayout(box3)

            self.style_drop = QtWidgets.QComboBox()
            self.style_drop.addItem("Fill")
            self.style_drop.addItem("Border")
            set_current_text(self.style_drop, self.data["style"])
            box3.addWidget(widget_with_label(self.style_drop, "appearance"))

            self.w = QtWidgets.QSpinBox()
            self.w.setValue(self.data["width"])
            self.w.setFixedSize(80, 25)
            box3.addWidget(widget_with_label(self.w, "width"))
            box3.addStretch(1)

        box4 = QtWidgets.QHBoxLayout()
        box4.setContentsMargins(70, 0, 0, 0)
        box4.setSpacing(0)
        set_layout.addLayout(box4)

        self.bm = QtWidgets.QCheckBox("bookmark")
        self.bm.setChecked(self.data["bookmark"])
        box4.addWidget(self.bm)

        self.box5 = QtWidgets.QHBoxLayout()
        self.box5.setContentsMargins(20, 0, 0, 0)
        self.box5.setSpacing(5)
        set_layout.addLayout(self.box5)

        self.zt = QtWidgets.QCheckBox()
        self.zt.setChecked(1)
        self.zt.setVisible(False)
        self.zt.setStyleSheet("background-color: #595959;")
        self.zt.stateChanged.connect(self.enableZ)
        self.box5.addWidget(self.zt)

        zval = self.data["zorder"]
        selected_bd = [n for n in nuke.selectedNodes() if n.Class() == "BackdropNode"]
        if selected_bd:
            zval = min([node["z_order"].value() for node in selected_bd]) - 1

        self.zorder = QtWidgets.QSpinBox(self)
        self.zorder.setFixedSize(80, 25)
        self.zorder.setRange(-999, 999)
        self.zorder.setValue(zval)
        self.box5.addWidget(widget_with_label(self.zorder, "Z Order"))
        self.box5.addStretch(1)

    def closeEvent(self, event):
        self.closed.emit()
        QtWidgets.QWidget.closeEvent(self, event)

    def changeColor(self, index):
        item_text = self.colBox.itemText(index)
        if item_text.startswith("#"):
            hex_color = item_text
        else:
            hex_color = rgb_to_hex(self.colors[index])
        self.colBox.setStyleSheet("background-color: %s;" % hex_color)
        if not self._editing and item_text != "":
            self.label.setText(item_text)

    def boldT(self):
        if self.boldv is False:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
            self.boldv = True
        else:
            self.boldb.setStyleSheet("font: bold; background-color: ;")
            self.boldv = False

    def italicT(self):
        if self.italicv is False:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
            self.italicv = True
        else:
            self.italicb.setStyleSheet("font: italic; background-color: ;")
            self.italicv = False

    def makeBackdrop(self):
        self.close()
        padding = self.data["padding"]
        text = self.label.text()
        alignment = "<" + self.format.currentText() + ">"
        color = rgb_to_interface(self.colors[self.colBox.currentIndex()])
        bold = "<b>" if self.boldv else ""
        italic = "<i>" if self.italicv else ""
        selected_nodes = nuke.selectedNodes()

        nuke.Undo.begin("Create Backdrop")
        try:
            if len(selected_nodes) > 0:
                bd_x = min([node.xpos() for node in selected_nodes])
                bd_y = min([node.ypos() for node in selected_nodes])
                bd_w = max([node.xpos() + node.screenWidth() for node in selected_nodes])
                bd_h = max([node.ypos() + node.screenHeight() for node in selected_nodes])
                bd_x = int(bd_x - padding)
                bd_y = int(bd_y - (padding + 60))
                bd_w = int(bd_w + padding)
                bd_h = int(bd_h + padding)

                node = nuke.nodes.BackdropNode(
                    xpos=bd_x,
                    bdwidth=bd_w - bd_x,
                    ypos=bd_y,
                    bdheight=bd_h - bd_y,
                    label=alignment + bold + italic + text,
                    z_order=self.zorder.value(),
                    tile_color=color,
                    bookmark=self.bm.isChecked(),
                    note_font=self.font.currentText(),
                    note_font_size=self.fsize.value(),
                    selected=True,
                )
            else:
                node = nuke.createNode("BackdropNode", inpanel=False)
                node["label"].setValue(alignment + bold + italic + text)
                node["z_order"].setValue(self.zorder.value())
                node["tile_color"].setValue(color)
                node["bookmark"].setValue(self.bm.isChecked())
                node["note_font"].setValue(self.font.currentText())
                node["note_font_size"].setValue(self.fsize.value())

            if NUKE_VERSION_MAJOR >= 12:
                node["appearance"].setValue(self.style_drop.currentText())
                node["border_width"].setValue(self.w.value())

            self._add_backdrop_controls(node, padding)
        except Exception as error:
            nuke.Undo.cancel()
            print("Error creating backdrop: {0}".format(error))
        else:
            nuke.Undo.end()

    def _add_backdrop_controls(self, node, padding_value):
        existing_knobs = node.knobs()
        for knob in existing_knobs:
            if knob == "User":
                user = node.knob(knob)
                user.setName("backdrop_settings")
                user.setLabel("Backdrop Settings")

        try:
            if not any("padding" in knob for knob in existing_knobs):
                padding = nuke.Int_Knob("padding", "Padding")
                node.addKnob(padding)
                padding.setValue(padding_value)

            if not any("snap" in knob for knob in existing_knobs):
                button = nuke.PyScript_Knob("snap", "Snap to selected nodes")
                button.setValue(
                    "this = nuke.thisNode()\n"
                    "selNodes = nuke.selectedNodes()\n"
                    "padding = this.knob('padding').value()\n"
                    "if len(selNodes)== 0:\n"
                    "\tpass\n"
                    "else:\n"
                    "\tbdX = min([node.xpos() for node in selNodes]) - padding\n"
                    "\tbdY = min([node.ypos() for node in selNodes]) - padding - 60\n"
                    "\tbdW = max([node.xpos() + node.screenWidth() for node in selNodes]) + padding\n"
                    "\tbdH = max([node.ypos() + node.screenHeight() for node in selNodes]) + padding\n"
                    "\tthis.knob('xpos').setValue(bdX)\n"
                    "\tthis.knob('ypos').setValue(bdY)\n"
                    "\tthis.knob('bdwidth').setValue(bdW-bdX)\n"
                    "\tthis.knob('bdheight').setValue(bdH-bdY)"
                )
                node.addKnob(button)
        except Exception:
            nuke.tprint("BackdropManager: failed to add backdrop controls")
            nuke.tprint(traceback.format_exc())

    def enableL(self):
        self.label.setEnabled(self.labelt.isChecked())

    def enableZ(self):
        self.zorder.setEnabled(self.zt.isChecked())

    def editBackdrop(self):
        self.close()
        text = self.label.text()
        z_order = self.zorder.value()
        alignment = "<" + self.format.currentText() + ">"

        if self.colBox.currentText().startswith("#"):
            color = hex_to_interface(self.colBox.currentText())
        else:
            color = rgb_to_interface(self.colors[self.colBox.currentIndex()])

        bold = "<b>" if self.boldv else ""
        italic = "<i>" if self.italicv else ""

        with active_dag_node():
            for selected in nuke.selectedNodes():
                if self.labelt.isChecked():
                    selected["label"].setValue(alignment + bold + italic + text)
                if self.zt.isChecked():
                    selected["z_order"].setValue(z_order)
                selected["tile_color"].setValue(color)
                selected["bookmark"].setValue(self.bm.isChecked())
                selected["note_font"].setValue(self.font.currentText())
                selected["note_font_size"].setValue(self.fsize.value())
                if NUKE_VERSION_MAJOR >= 12:
                    selected["appearance"].setValue(self.style_drop.currentText())
                    selected["border_width"].setValue(self.w.value())

    def switch(self):
        with active_dag_node():
            selected = nuke.selectedNodes()
            for item in selected:
                item.setSelected(False)
                if item.Class() == "BackdropNode":
                    item.setSelected(True)

            selection_count = len(nuke.selectedNodes())
            if selection_count == 1:
                selected_node = nuke.selectedNode()
                label = selected_node["label"].value()
                color = selected_node["tile_color"].value()

            self.setWindowTitle("Edit backdrop")
            self._editing = True
            self.buttonBox.accepted.disconnect()
            self.buttonBox.accepted.connect(self.editBackdrop)

            for i in range(self.colBox.count()):
                self.colBox.setItemText(i, "")

            if selection_count > 1:
                self.labelt.setVisible(True)
                self.box6.setContentsMargins(16, 0, 0, 0)
                self.zt.setVisible(True)
                self.box5.setContentsMargins(0, 0, 0, 0)
            elif selection_count == 1:
                if "<center>" in label:
                    set_current_text(self.format, "center")
                else:
                    set_current_text(self.format, "left")

                self.boldv = "<b>" in label
                self.boldb.setStyleSheet(
                    "font: bold; background-color: #787878;"
                    if self.boldv
                    else "font: bold; background-color: ;"
                )

                self.italicv = "<i>" in label
                self.italicb.setStyleSheet(
                    "font: italic; background-color: #787878;"
                    if self.italicv
                    else "font: italic; background-color: ;"
                )

                color = rgb_to_hex(interface_to_rgb(color))
                label = label.split(">")[-1]
                matched_index = next(
                    (i for i, preset in enumerate(self.colors) if rgb_to_hex(preset) == color),
                    None,
                )
                if matched_index is not None:
                    self.colBox.setCurrentIndex(matched_index)
                else:
                    self.colBox.addItem(color)
                    model = self.colBox.model()
                    row = self.colBox.count() - 1
                    model.setData(model.index(row, 0), QtGui.QColor(color), QtCore.Qt.BackgroundRole)
                    self.colBox.setCurrentIndex(row)
                self.colBox.setStyleSheet("background-color: %s;" % color)
                self.label.setText(label)
                self.zorder.setValue(selected_node["z_order"].value())
                if NUKE_VERSION_MAJOR >= 12:
                    set_current_text(self.style_drop, selected_node["appearance"].value())
                    self.w.setValue(selected_node["border_width"].value())
                self.bm.setChecked(selected_node["bookmark"].value())
                set_current_text(self.font, selected_node["note_font"].value())
                self.fsize.setValue(selected_node["note_font_size"].value())
            else:
                self.zorder.setValue(self.data["zorder"])