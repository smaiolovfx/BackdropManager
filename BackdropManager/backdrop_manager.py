import nuke
from nukescripts import panels
import os
from functools import partial
import traceback
import colorsys
import datetime

from BackdropManager.info import __version__, __date__

try:
    # Prefer Qt.py when available
    from Qt import QtCore, QtGui, QtWidgets
    from Qt.QtCore import Qt
except ImportError:
    try:
        # PySide2 for default Nuke 11
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Qt
    except ImportError:
        # Or PySide for Nuke 10
        from PySide import QtCore, QtGui, QtGui as QtWidgets
        from PySide.QtCore import Qt
        
today = datetime.date.today()
year = today.year

nuke.tprint('BackdropManager v{0}, built {1}.\n'
            'Copyright (c) 2022-{2} Samantha Maiolo.'
            ' All Rights Reserved.'.format(__version__, __date__, year))    
        
icon_path = os.path.expanduser("~/.nuke/BackdropManager/icons/")

nuke_ver = nuke.NUKE_VERSION_MAJOR

DAG_TITLE = "Node Graph"
DAG_OBJECT_NAME = "DAG"

# Get DAG
def get_dag_widgets(visible=True):
    """
    Gets all Qt objects with DAG in the object name. Thanks to Erwan Leroy.
    """
    dags = []
    all_widgets = QtWidgets.QApplication.instance().allWidgets()
    for widget in all_widgets:
        if DAG_OBJECT_NAME in widget.objectName():
            if not visible or (visible and widget.isVisible()):
                dags.append(widget)
    return dags

def get_current_dag():
    """
    Returns:
        QtWidgets.QWidget: The currently active DAG
    """
    visible_dags = get_dag_widgets(visible=True)
    for dag in visible_dags:
        if dag.hasFocus():
            return dag

    # If None had focus, and we have at least one, use the first one
    if visible_dags:
        return visible_dags[0]
    return None

def get_dag_node(dag_widget):
    """ Get a DAG node for a given dag widget. """
    title = str(dag_widget.windowTitle())
    if DAG_TITLE not in title:
        return None
    if title == DAG_TITLE:
        return nuke.root()
    return nuke.toNode(title.replace(" " + DAG_TITLE, ""))
    
def wrapped(func):
    """ Executes the function argument in the currently active DAG. """
    def wrapper(*args, **kwargs):
        active_dag = get_current_dag()
        dag_node = None
        if active_dag:
            node = get_dag_node(active_dag)
            with node:
               result = func(*args, **kwargs)
               return result
    return wrapper

def interface2rgb(hexValue, normalize = True):
    '''
    Convert a color stored as a 32 bit value as used by nuke for interface colors to normalized rgb values.
    '''
    return [(0xFF & hexValue >>  i) / 255.0 for i in [24,16,8]]

def rgb2hex(rgbaValues):
    '''
    Convert a color stored as normalized rgb values to a hex.
    '''
    rgbaValues = [int(i * 255) for i in rgbaValues]

    if len(rgbaValues) < 3:
        return

    return '#%02x%02x%02x' % (rgbaValues[0],rgbaValues[1],rgbaValues[2])

def hex2rgb(hexColor):
    '''
    Convert a color stored as hex to rgb values.
    '''
    hexColor = hexColor.lstrip('#')
    return tuple(int(hexColor[i:i+2], 16) for i in (0, 2 ,4))    
    
def hex2interface(hexColor):
    '''
    Convert a color stored as hex to a 32 bit value as used by nuke for interface colors.
    '''    
    hexColor = hexColor.lstrip('#')
    return int(hexColor+'00', 16)    

def rgb2interface(rgb):
    '''
    Convert a color stored as rgb values to a 32 bit value as used by nuke for interface colors.
    '''
    return int('%02x%02x%2x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255),1),16)

def _widget_with_label(towrap, text):
    """Wraps the given widget in a layout, with a label to the left"""
    w = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(5)
    layout.setContentsMargins(0,0,0,0)
    label = QtWidgets.QLabel(text)
    layout.addWidget(label)
    layout.addWidget(towrap)
    w.setLayout(layout)
    return w     
    
def setCurrentText(widget, text):
    """ Change setCurrentText to a function to work with Nuke10"""
    index = widget.findText(text, QtCore.Qt.MatchFixedString)
    if index >= 0:
        widget.setCurrentIndex(index)            

class DragButton(QtWidgets.QPushButton):
    def set_data(self, data):
        self.data = data
        
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MiddleButton:
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            drag.setMimeData(mime)

            pixmap = QtGui.QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

def filter(list):
    """ Filter through selected backdrops for the largest. """
    backdrop_dict = {}
    area = []
    for x in list:
        if x.Class() == 'BackdropNode':
            a = int(x['bdwidth'].value() * x['bdheight'].value())
            backdrop_dict[x] = a
            area.append(a)
    area.sort()
    return(area, backdrop_dict)

def snap():    
    """ Snap backdrops to the selected nodes. """
    settings = Overrides()        
    d = settings.restore()        
    selNodes = nuke.selectedNodes()
    padding = d['padding']
    
    if len(selNodes) == 0: 
        return
        
    else:
        a = filter(selNodes)[0]
        b = filter(selNodes)[1]
        
        if a == []:          
            return
            
        else:
            nuke.Undo.begin()
            largest = [k for k, v in b.items() if v == a[-1]][0]
            selNodes.remove(largest)
            this = largest
            bdX = min([node.xpos() for node in selNodes]) - padding
            bdY = min([node.ypos() for node in selNodes]) - padding - 60
            bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) + padding
            bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) + padding
            
            this.knob('bdwidth').setValue(bdW-bdX)
            this.knob('xpos').setValue(bdX)                
            this.knob('bdheight').setValue(bdH-bdY)  
            this.knob('ypos').setValue(bdY)
            nuke.Undo.end() 

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

        self.button.setToolTip("Sets the key sequence used to make a backdrops. Click to start recording.")
        self.clearButton.setToolTip("Clear the key sequence.")

    def setShortcut(self, shortcut):
        """Sets the initial shortcut to display."""
        self.button.setKeySequence(shortcut)

    def shortcut(self):
        """Returns the currently set key sequence."""
        return self.button.keySequence()

    def clear(self):
        """Empties the displayed shortcut."""
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
        self._modifierlessAllowed = True  # True allows "b" as a shortcut, False requires shift/alt/ctrl/etc
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
            s = self._recseq.toString(QtGui.QKeySequence.NativeText).replace('&', '&&')
            if self._modifiers:
                if s: s += ","
                s += QtGui.QKeySequence(self._modifiers).toString(QtGui.QKeySequence.NativeText)
            elif self._recseq.isEmpty():
                s = "Input"
            s += " ..."
        else:
            s = self._seq.toString(QtGui.QKeySequence.NativeText).replace('&', '&&')
        self.setText(s)

    def isRecording(self):
        return self._isrecording

    def event(self, ev):
        if self._isrecording:
            # prevent Qt from special casing Tab and Backtab
            if ev.type() == QtCore.QEvent.KeyPress:
                self.keyPressEvent(ev)
                return True
        return QtWidgets.QPushButton.event(self, ev)

    def keyPressEvent(self, ev):
        if not self._isrecording:
            return QtWidgets.QPushButton.keyPressEvent(self, ev)
        if ev.isAutoRepeat():
            return
        modifiers = ev.modifiers()

        ev.accept()

        all_modifiers = (-1, Qt.Key_Shift, Qt.Key_Control, Qt.Key_AltGr, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_Menu)

        key = ev.key()
        # check if key is a modifier or a character key without modifier (and if that is allowed)
        if (
            # don't append the key if the key is -1 (garbage) or a modifier ...
            key not in all_modifiers
           # or if this is the first key and without modifier and modifierless keys are not allowed
            and (self._modifierlessAllowed
                 or self._recseq.count() > 0
                 or modifiers & ~Qt.SHIFT
                 or not ev.text()
                 or (modifiers & Qt.SHIFT
                     and key in (Qt.Key_Return, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab,
                                 Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Escape)))):

            # change Shift+Backtab into Shift+Tab
            if key == Qt.Key_Backtab and modifiers & Qt.SHIFT:
                key = Qt.Key_Tab | modifiers

            # remove the Shift modifier if it doen't make sense..
            elif (Qt.Key_Exclam <= key <= Qt.Key_At
                  # ... e.g ctrl+shift+! is impossible on, some,
                  # keyboards (because ! is shift+1)
                  or Qt.Key_Z < key <= 0x0ff):
                key = key | (modifiers & ~int(Qt.SHIFT))

            else:
                key = key | modifiers

            # append max number of keystrokes
            if self._recseq.count() < self.MAX_NUM_KEYSTROKES:
                l = list(self._recseq)
                l.append(key)
                self._recseq = QtGui.QKeySequence(*l)

        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def keyReleaseEvent(self, ev):
        if not self._isrecording:
            return QtWidgets.QPushButton.keyReleaseEvent(self, ev)
        modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
        ev.accept()

        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def hideEvent(self, ev):
        if self._isrecording:
            self.cancelRecording()
        QtWidgets.QPushButton.hideEvent(self, ev)

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
        self._modifiers = int(QtWidgets.QApplication.keyboardModifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
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

# Settings JSON file
def _load_yaml(path):
    def _load_internal():
        import json
        if not os.path.isfile(path):
            print("Settings file %r does not exist" % (path))
            return
        f = open(path)
        overrides = json.load(f)
        f.close()
        return overrides

    # Catch any errors, print traceback and continue
    try:
        return _load_internal()
    except Exception:
        print("Error loading %r" % path)
        import traceback
        traceback.print_exc()

        return None

def _save_yaml(obj, path):
    def _save_internal():
        import json
        ndir = os.path.dirname(path)
        if not os.path.isdir(ndir):
            try:
                os.makedirs(ndir)
            except OSError as e:
                if e.errno != 17:  # errno 17 is "already exists"
                    raise

        f = open(path, "w")
        json.dump(obj, fp=f, sort_keys=True, indent=1, separators=(',', ': '))
        f.write("\n")
        f.close()

    # Catch any errors, print traceback and continue
    try:
        _save_internal()
    except Exception:
        print("Error saving BackdropManager settings")
        import traceback
        traceback.print_exc()

class Overrides(object):
    def __init__(self):
        self.settings_path = os.path.expanduser("~/.nuke/BackdropManager/backdropmanager_settings.json")

    def save(self):
        settings = {
            'settings': self.defaults,
            'version': 3,
                    }
        _save_yaml(obj=settings, path=self.settings_path)
       
        nuke_setup()

    def clear(self):
        # Default
        self.defaults = {
            'colors': [(0.26, 0.26, 0.26), (0.32, 0.255, 0.19), (0.32, 0.19, 0.19), (0.32, 0.19, 0.255), (0.255, 0.19, 0.32), (0.19, 0.19, 0.32), (0.19, 0.255, 0.32), (0.19, 0.32, 0.19)],
            'labels': ["", "", "", "", "", "", "", ""],
            'shortcut': 'CTRL+B',
            'snap': 'CTRL+SHIFT+B',
            'padding': 40,
            'style': 'Fill',
            'width': 15,
            'zorder': 0,
            'bookmark': 1,
            'font': 'Source Code Pro Light',
            'font_size': 40,
            'bold': False,
            'italic': False,
            'align': 'center'
                        }
        self.save()

    def restore(self):
        """Load the settings from disc, and update Nuke
        """
        settings = _load_yaml(path=self.settings_path)

        self.defaults = {
            'colors': [(0.26, 0.26, 0.26), (0.32, 0.255, 0.19), (0.32, 0.19, 0.19), (0.32, 0.19, 0.255), (0.255, 0.19, 0.32), (0.19, 0.19, 0.32), (0.19, 0.255, 0.32), (0.19, 0.32, 0.19)],
            'labels': ["", "", "", "", "", "", "", ""],
            'shortcut': 'CTRL+B',
            'snap': 'CTRL+SHIFT+B',
            'padding': 40,
            'style': 'Fill',
            'width': 15,
            'zorder': 0,
            'bookmark': 1,
            'font': 'Source Code Pro Light',
            'font_size': 40,
            'bold': False,
            'italic': False,
            'align': 'center'
                        }

        if settings is None:
            self.clear()
            return self.defaults

        elif int(settings['version']) >= 2:
            self.defaults = settings['settings']
            return self.defaults

        else:
            nuke.warning("Wrong version of backdrop manager config, nothing loaded (version %s loaded, version 3 is the latest), path was %r. Please either delete your settings file or re-download the latest BackdropManager." % (
                int(settings['version']),
                self.settings_path))
            return

    def load(self):
        settings = {
            'settings': self.defaults,
            'version': 3,
                    }
        return settings

class BackdropManagerSettings(QtWidgets.QDialog):
    closed = QtCore.Signal()

    def __init__(self):
        QtWidgets.QDialog.__init__(self)        
        
        self.setAcceptDrops(True)

        # Load settings from disc, and into Nuke
        self.settings = Overrides()
        d = self.settings.restore()

        # Window setup
        self.setWindowTitle("Backdrop Manager Settings")
        self.setMinimumSize(470, 700)
        self.setWhatsThis("This sets the default values for backdrop settings. Values can be changed when making a backdrop. Add or change color boxes to set presets for backdrop colors.")

        # Try moving to last opened position
        try:
            self.move(d['xpos'], d['ypos'])
        except: pass
                
        # Stack widgets atop each other
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)
        
        # Settings box
        set_group = QtWidgets.QGroupBox("Settings")
        set_layout = QtWidgets.QVBoxLayout()
        set_layout.setSpacing(10)
        set_layout.setContentsMargins(10,10,10,10)
        set_group.setLayout(set_layout)

        self.layout.addWidget(set_group, 1)

        # Shortcut box
        box = QtWidgets.QHBoxLayout()
        box.setContentsMargins(20,0,0,0)
        box.setSpacing(0)
        set_layout.addLayout(box)

         # Shortcut
        self.ks = QtGui.QKeySequence(d['shortcut'])
        self.shortcut_widget = KeySequenceWidget()
        self.shortcut_widget.setShortcut(self.ks)
        self.shortcut_widget.keySequenceChanged.connect(self.updateSC)
        box.addWidget(_widget_with_label(self.shortcut_widget, "Shortcut"))
        
        box.addStretch(1)        
        
        # Snap box
        box7 = QtWidgets.QHBoxLayout()
        box7.setContentsMargins(40,0,0,0)
        box7.setSpacing(10)
        set_layout.addLayout(box7)
        
        # Snap
        self.ks = QtGui.QKeySequence(d['snap'])
        self.snap_widget = KeySequenceWidget()
        self.snap_widget.setShortcut(self.ks)
        self.snap_widget.keySequenceChanged.connect(self.updateSnap)
        box7.addWidget(_widget_with_label(self.snap_widget, "Snap"))
        
        # Padding
        self.p = d['padding']

        self.psize = QtWidgets.QSpinBox(self)
        self.psize.setToolTip("Set default snap padding size.")
        self.psize.setFixedSize(80,24)
        self.psize.setRange(0,999)
        self.psize.setValue(self.p)
        self.psize.valueChanged.connect(self.updateP)
        box7.addWidget(_widget_with_label(self.psize, "padding"))        
        
        box7.addStretch(1)        

        # Font box
        box2 = QtWidgets.QHBoxLayout()
        box2.setContentsMargins(45,0,0,0)
        box2.setSpacing(5)
        set_layout.addLayout(box2)
        
        label = QtWidgets.QLabel("font")
        box2.addWidget(label)

        # Font
        self.f = d['font']

        self.font = QtWidgets.QFontComboBox()
        self.font.setToolTip("Set default label font.")
        setCurrentText(self.font, self.f)
        box2.addWidget(self.font)

        # Font size
        self.fs = d['font_size']

        self.fsize = QtWidgets.QSpinBox(self)
        self.fsize.setToolTip("Set default label font size.")
        self.fsize.setFixedSize(80,24)
        self.fsize.setRange(0,999)
        self.fsize.setValue(self.fs)
        self.fsize.valueChanged.connect(self.updateFS)
        box2.addWidget(self.fsize)
        
        # Bold button
        self.boldv = d['bold']  
              
        self.boldb = QtWidgets.QPushButton("B")
        self.boldb.setStyleSheet("font: bold;")
        self.boldb.setToolTip("Make label font bold by default.")
        self.boldb.setFixedSize(20,20)
        if self.boldv is True:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
        self.boldb.clicked.connect(self.bold)
        box2.addWidget(self.boldb)
        
        # Italic button
        self.italicv = d['italic']
         
        self.italicb = QtWidgets.QPushButton("I")
        self.italicb.setStyleSheet("font: italic;")
        self.italicb.setToolTip("Make label font italic by default.")
        self.italicb.setFixedSize(20,20)
        if self.italicv is True:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")        
        self.italicb.clicked.connect(self.italic)        
        box2.addWidget(self.italicb)
        
        box2.addStretch(1)
        
        # Label format box
        box3 = QtWidgets.QHBoxLayout()
        box3.setContentsMargins(10,0,0,0)
        box3.setSpacing(0)
        set_layout.addLayout(box3)
        
       # Format dropdown
        self.f = d['align']

        self.format = QtWidgets.QComboBox()
        self.format.addItem('left')
        self.format.addItem('center')
        self.format.setToolTip("Set default label text alignment.")
        setCurrentText(self.format, self.f)
        box3.addWidget(_widget_with_label(self.format, "label align"))
        
        box3.addStretch(1)
        
        if nuke_ver >= 12:
            # Style box
            box4 = QtWidgets.QHBoxLayout()
            box4.setContentsMargins(0,0,0,0)
            box4.setSpacing(5)
            set_layout.addLayout(box4)
            
            label = QtWidgets.QLabel("appearance")
            box4.addWidget(label)        
    
            # Style dropdown
            self.sd = d['style']
    
            self.style_drop = QtWidgets.QComboBox()
            self.style_drop.addItem('Fill')
            self.style_drop.addItem('Border')
            self.style_drop.setToolTip("Set default style.")
            setCurrentText(self.style_drop, self.sd)
            box4.addWidget(self.style_drop)
    
            # Width
            self.wval = d['width']
    
            self.w = QtWidgets.QSpinBox()
            self.w.setToolTip("Set default border width value.")
            self.w.setFixedSize(80,24)
            self.w.setValue(self.wval)
            self.w.valueChanged.connect(self.updateW)
            box4.addWidget(_widget_with_label(self.w, "width"))
            
            box4.addStretch(1)

        # Box for bookmark
        box5 = QtWidgets.QHBoxLayout()
        box5.setContentsMargins(73,0,0,0)
        box5.setSpacing(0)
        set_layout.addLayout(box5)

        # Checkbox
        self.bval = d['bookmark']

        self.bm = QtWidgets.QCheckBox("bookmark")
        self.bm.setToolTip("Set default bookmark value.")
        self.bm.setChecked(self.bval)
        self.bm.stateChanged.connect(self.updateB)
        box5.addWidget(self.bm)

        # Box for Z
        box6 = QtWidgets.QHBoxLayout()
        box6.setContentsMargins(23,0,260,0)
        box6.setSpacing(0)
        set_layout.addLayout(box6)

        # Z order
        self.zval = d['zorder']

        self.zorder = QtWidgets.QSpinBox(self)
        self.zorder.setToolTip("Set default Z order value.")
        self.zorder.setFixedSize(80,24)
        self.zorder.setRange(-999,999)
        self.zorder.setValue(self.zval)
        self.zorder.valueChanged.connect(self.updateZ)
        box6.addWidget(_widget_with_label(self.zorder, "Z Order"))
        
        box6.addStretch(1)

        # Box group
        box_group = QtWidgets.QGroupBox("Color Presets")
        box_group.setContentsMargins(0,25,0,0)
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(15)
        self.box_layout = QtWidgets.QGridLayout()
        self.box_layout.setSpacing(15)
        vbox.addLayout(self.box_layout)
        box_group.setLayout(vbox)

        self.layout.addWidget(box_group, 2)   

        # Get colors from file
        self.colors = d['colors']
        
        # Get titles from file
        try:
            self.labels = d['labels']
        except:
            self.labels = []
            for c in self.colors:
                self.labels.append("")
                d['labels'] = self.labels
                self.settings.save()

        self.c = 0
        self.row = 0
        
        # Make boxes
        self.boxes = []
        self.titles = []
        
        for color, label in zip(self.colors, self.labels):
            idx = self.colors.index(color)
            btn = DragButton()
            self.boxes.append(btn)
            btn.setToolTip("Click to change color.")
            btn.setAutoFillBackground(True)
            p = btn.palette()
            p.setColor(btn.backgroundRole(), QtGui.QColor(rgb2hex(color)))
            btn.setPalette(p)
            btn.set_data(color)
            btn.setFixedSize(20,20)
            
            title = QtWidgets.QLineEdit()
            self.titles.append(title)
            title.setToolTip("Enter default label.")
            title.setText(label)
    
            self.row += 1
            self.box_layout.addWidget(btn, self.row -1, 0)
            self.box_layout.addWidget(title, self.row -1, 1)
    
            btn.clicked.connect(partial(self.btnClicked, idx, btn))
    
        # Make +/- Box
        pmbox = QtWidgets.QHBoxLayout()
        pmbox.setContentsMargins(0,0,0,0)
        pmbox.setSpacing(10)
        pmbox.addStretch(375)
        vbox.addLayout(pmbox)
        
        # Get UI Colors
        p = nuke.toNode('preferences')
        pcol = p['UIBackColor'].value()
        pcol = interface2rgb(pcol)
        pcol = rgb2hex(pcol)        

        # Make minus button (TO DO: Add functionality to select box to remove)
        minb = QtWidgets.QPushButton("-")
        minb.setToolTip("Remove last color box.")
        minb.setStyleSheet("background-color: %s;" % pcol)        
        minb.setFixedSize(20,20)
        minb.clicked.connect(self.min)
        pmbox.addWidget(minb)

        # Make plus button
        addb = QtWidgets.QPushButton("+")
        addb.setToolTip("Add a new color box.")
        addb.setStyleSheet("background-color: %s;" % pcol)       
        addb.clicked.connect(self.add) 
        addb.setFixedSize(20,20)        
        pmbox.addWidget(addb)

        # Button box
        box7 = QtWidgets.QHBoxLayout()
        box7.setSpacing(60)
        self.layout.addLayout(box7)

        # Reset panel button
        button_default = QtWidgets.QPushButton("Set to default")
        button_default.setToolTip("Set ALL values back to default, including colors.")
        button_default.clicked.connect(self.default)
        box7.addWidget(button_default)
        self.button_default = button_default

        # Close panel button
        button_close = QtWidgets.QPushButton("Save")
        button_close.setToolTip("Save settings.")
        button_close.clicked.connect(self.closeSave)
        box7.addWidget(button_close)
        self.button_close = button_close
        self.button_close.setFocus()
        
        button_cancel = QtWidgets.QPushButton("Cancel")
        button_cancel.setToolTip("Close window and revert back to previous saved settings.")
        button_cancel.clicked.connect(self.close)
        box7.addWidget(button_cancel)
        self.button_cancel = button_cancel
        
    def min(self):
        """Remove box"""
        for w in [self.boxes, self.titles]:
            self.box_layout.removeWidget(w[-1])
            w[-1].deleteLater()
            w[-1] = None
            w.pop(-1)
            
        self.colors.pop(-1)
        
        try:
            self.labels.pop(-1)
        except: pass
        
        self.row -= 1
        
        self.box_layout.update()

    def add(self):
        """Add a new box"""
        col = nuke.getColor()
        if col:
            col = interface2rgb(col)        
            self.colors.append(col)
            idx = len(self.boxes) - 1
            
            btn = DragButton()
            self.boxes.append(btn)
            btn.setToolTip("Click to change color.")
            btn.setAutoFillBackground(True)
            p = btn.palette()
            p.setColor(btn.backgroundRole(), QtGui.QColor(rgb2hex(col)))
            btn.setPalette(p)
            btn.set_data(col)
            btn.setFixedSize(20,20)
            
            title = QtWidgets.QLineEdit()
            self.titles.append(title)
            self.labels.append("")
            title.setToolTip("Enter default label.")

            self.row += 1
            self.box_layout.addWidget(btn, self.row -1, 0)
            self.box_layout.addWidget(title, self.row -1, 1)
            
            self.box_layout.update()

            btn.clicked.connect(partial(self.btnClicked, idx, btn))

    def updateFS(self):
        """Saves font size"""
        val = self.fsize.value()
        d = self.settings.restore()
        d['font_size'] = val
        
    def updateP(self):
        """Saves padding"""
        val = self.psize.value()
        d = self.settings.restore()
        d['padding'] = val        
       
    def updateSC(self):
        """Saves shortcut"""
        val = self.shortcut_widget.shortcut().toString()
        d = self.settings.restore()
        d['shortcut'] = val
        
    def updateSnap(self):
        """Saves snap shortcut"""
        val = self.snap_widget.shortcut().toString()
        d = self.settings.restore()
        d['snap'] = val        
               
    def updateW(self):
        """Saves width"""
        val = self.w.value()
        d = self.settings.restore()
        d['width'] = val
               
    def updateZ(self):
        """Saves zorder"""
        val = self.zorder.value()
        d = self.settings.restore()
        d['zorder'] = val
    
    def bold(self):
        """Saves bold"""
        if self.boldv == False:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
            self.boldv = True
        else:
            self.boldb.setStyleSheet("font: bold; background-color: ;")
            self.boldv = False
        d = self.settings.restore()
        d['bold'] = self.boldv  
        
    def italic(self):
        """Saves italic"""
        if self.italicv == False:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
            self.italicv = True
        else:
            self.italicb.setStyleSheet("font: italic; background-color: ;")
            self.italicv = False
        d = self.settings.restore()
        d['italic'] = self.italicv        
               
    def updateB(self):
        """Saves bookmark"""
        val = self.bm.isChecked()
        d = self.settings.restore()
        d['bookmark'] = val
               
    def btnClicked(self, color_idx, btn):
        """Function to set a new default color"""
        color = self.colors[color_idx]
        color = int('%02x%02x%2x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255),1),16)
         
        col = nuke.getColor(color)
        col = interface2rgb(col)
       
        self.colors[color_idx] = col
     
        col = rgb2hex(col)
        btn.setStyleSheet("background-color: %s;" % (col))
               
    def default(self):
        """Sets settings to default"""   
        mb = QtWidgets.QMessageBox(self)
        mb.setText("Clear all settings?")
        mb.setIcon(QtWidgets.QMessageBox.Warning)
        mb.setStandardButtons(QtWidgets.QMessageBox.Reset | QtWidgets.QMessageBox.Cancel)
        mb.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        ret = mb.exec_()

        if ret == QtWidgets.QMessageBox.Reset:
            self.settings.clear()
            self.close()
            gui()
        elif ret == QtWidgets.QMessageBox.Cancel:
            pass
        else:
            raise RuntimeError("Unhandled button")
           
    def closeSave(self, evt):
        """Save when closing the UI"""
        d = self.settings.load()
        s = d['settings']
        s['font'] = self.font.currentText()
        s['align'] = self.format.currentText()
        s['xpos'] = self.pos().x()
        s['ypos'] = self.pos().y()
        
        s['colors'] = self.colors
        for w in self.titles:
            self.labels[self.titles.index(w)] = w.text()
        s['labels'] = self.labels
        
        if nuke_ver >= 12:
            s['style'] = self.style_drop.currentText()
            
        self.settings.save()
        self.close()
        self.closed.emit()
       
    def closeEvent(self, evt):
        self.closed.emit()
        QtWidgets.QWidget.closeEvent(self, evt)
       
def load_settings():
    """
    Load the settings from disc
    Could be called from menu.py (see module docstring at start of file for an example)
    """
    s = Overrides()
    s.restore()
   
_sew_instance = None

def gui():
   
    load_settings()
   
    global _sew_instance

    if _sew_instance is not None:
        # Already an instance (make it really obvious - focused, in front and under cursor, like other Nuke GUI windows)
        _sew_instance.show()
        _sew_instance.setFocus()
        _sew_instance.activateWindow()
        _sew_instance.raise_()
        return

    # Make a new instance, keeping it in a global variable to avoid multiple instances being opened
    _sew_instance = BackdropManagerSettings()

    def when_closed():
        global _sew_instance
        _sew_instance = None

    _sew_instance.closed.connect(when_closed)

    modal = False
    if modal:
        _sew_instance.exec_()
    else:
        _sew_instance.show()
       
""" Start shortcut UI """

class BackdropManagerUI(QtWidgets.QDialog):
    closed = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)

        # Get settings data
        o = Overrides()
        self.data = o.restore()

        # Window setup
        self.setWindowTitle("Make backdrop")
        self.setMinimumSize(450, 300)

        self.setFocus()

        # Stack widgets atop each other
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(25)
        self.setLayout(layout)

        # Settings box
        set_group = QtWidgets.QGroupBox("Backdrop")
        set_layout = QtWidgets.QVBoxLayout()
        set_layout.setSpacing(10)
        set_group.setLayout(set_layout)

        layout.addWidget(set_group)
       
        # Color box
        box = QtWidgets.QHBoxLayout()
        box.setContentsMargins(40,0,0,0)
        box.setSpacing(0)
        set_layout.addLayout(box)    

        # Color dropdown        
        self.colBox = QtWidgets.QComboBox()
        self.colBox.setFixedSize(100,25)
        self.colors = self.data['colors']
        
        try:
            self.labels = self.data['labels']
        except:
            self.labels = []
            for c in self.colors:
                self.labels.append("")
                self.data['labels'] = self.labels
                o.save()
        
        try:
            baseCol = rgb2hex(self.colors[0])
        except:
            baseCol = None
            
            self.colBox.setAutoFillBackground(True)
            p = self.colBox.palette()
            p.setColor(self.colBox.backgroundRole(), QtGui.QColor(baseCol))
            self.colBox.setPalette(p)
            
        model = self.colBox.model()
        for color, label in zip(self.colors, self.labels):
            row = self.colors.index(color)
            self.colBox.addItem(label)
            model.setData(model.index(row, 0), QtGui.QColor(rgb2hex(color)), QtCore.Qt.BackgroundRole)
        box.addWidget(_widget_with_label(self.colBox, "color"))

        self.colBox.activated.connect(self.changeColor)
        
        box.addStretch(1)
       
        # Label box
        self.box6 = QtWidgets.QHBoxLayout()
        self.box6.setContentsMargins(40,0,0,0)
        self.box6.setSpacing(10)
        set_layout.addLayout(self.box6)
        
        # Label toggle (visible in edit mode)
        self.labelt = QtWidgets.QCheckBox()
        self.labelt.setChecked(1)
        self.labelt.setVisible(False)
        self.labelt.setStyleSheet("background-color: #595959;")        
        self.labelt.stateChanged.connect(self.enableL)
        self.box6.addWidget(self.labelt)        
       
        # Label
        self.label = QtWidgets.QLineEdit()
        self.label.setFixedWidth(200)
        self.label.setText("")
        self.box6.addWidget(_widget_with_label(self.label, "label"))
        
        # Format
        fm = self.data['align']
        self.format = QtWidgets.QComboBox()
        self.format.addItem('left')
        self.format.addItem('center')
        setCurrentText(self.format, fm)
        self.box6.addWidget(_widget_with_label(self.format, "align"))
        
        self.box6.addStretch(1)
       
        # Font box
        box2 = QtWidgets.QHBoxLayout()
        box2.setContentsMargins(45,0,0,0)
        box2.setSpacing(0)
        set_layout.addLayout(box2)
       
        # Font
        f = self.data['font']
     
        self.font = QtWidgets.QFontComboBox()
        setCurrentText(self.font, f)
        box2.addWidget(_widget_with_label(self.font, "font"))
       
        # Font size
        fs = self.data['font_size']
       
        self.fsize = QtWidgets.QSpinBox(self)
        self.fsize.setFixedSize(80,25)
        self.fsize.setRange(0,999)               
        self.fsize.setValue(fs)
        box2.addWidget(self.fsize)
        
        # Bold button
        self.boldv = self.data['bold']
              
        self.boldb = QtWidgets.QPushButton("B")
        self.boldb.setStyleSheet("font: bold;")
        self.boldb.setFixedSize(20,20)
        if self.boldv is True:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
        self.boldb.clicked.connect(self.boldT)
        box2.addWidget(self.boldb)
        
        # Italic button
        self.italicv = self.data['italic']
         
        self.italicb = QtWidgets.QPushButton("I")
        self.italicb.setStyleSheet("font: italic;")
        self.italicb.setFixedSize(20,20)
        if self.italicv is True:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")        
        self.italicb.clicked.connect(self.italicT)        
        box2.addWidget(self.italicb)     
        
        box2.addStretch(1)   
        
        if nuke_ver >= 12:   
            # Style box
            box3 = QtWidgets.QHBoxLayout()
            box3.setContentsMargins(0,0,0,0)
            box3.setSpacing(10)
            set_layout.addLayout(box3)
           
            # Style dropdown
            sd = self.data['style']
                           
            self.style_drop = QtWidgets.QComboBox()
            self.style_drop.addItem('Fill')
            self.style_drop.addItem('Border')
            setCurrentText(self.style_drop, sd)
            box3.addWidget(_widget_with_label(self.style_drop, "appearance"))
    
            # Width
            wval = self.data['width']
                   
            self.w = QtWidgets.QSpinBox()
            self.w.setValue(wval)
            self.w.setFixedSize(80,25)
            box3.addWidget(_widget_with_label(self.w, "width"))
            
            box3.addStretch(1)
       
        # Bookmark box
        box4 = QtWidgets.QHBoxLayout()
        box4.setContentsMargins(70,0,0,0)
        box4.setSpacing(0)
        set_layout.addLayout(box4)
       
        # Checkbox
        bval = self.data['bookmark']
               
        self.bm = QtWidgets.QCheckBox("bookmark")
        self.bm.setChecked(bval)
        box4.addWidget(self.bm)
       
        # Z order box
        self.box5 = QtWidgets.QHBoxLayout()
        self.box5.setContentsMargins(20,0,0,0)
        self.box5.setSpacing(5)
        set_layout.addLayout(self.box5)
        
        # Z order toggle (visible in edit mode)
        self.zt = QtWidgets.QCheckBox()
        self.zt.setChecked(1)
        self.zt.setVisible(False)
        self.zt.setStyleSheet("background-color: #595959;")        
        self.zt.stateChanged.connect(self.enableZ)
        self.box5.addWidget(self.zt) 
       
        # Z order
        zval = self.data['zorder']
       
        """Check if trying to make a backdrop around a backdrop, if so, default to z order below"""
        selected_bd = [n for n in nuke.selectedNodes() if n.Class() == 'BackdropNode']
        # if there are backdropNodes in our list put the new one immediately behind the farthest one
        if selected_bd:
            zval = min([node['z_order'].value() for node in selected_bd]) - 1        
             
        self.zorder = QtWidgets.QSpinBox(self)
        self.zorder.setFixedSize(80,25)
        self.zorder.setRange(-999,999)
        self.zorder.setValue(zval)
        self.box5.addWidget(_widget_with_label(self.zorder, "Z Order"))
        
        self.box5.addStretch(1)
   
        # Close panel button
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(wrapped(self.makeBackdrop))
        self.buttonBox.rejected.connect(self.close)
       
        self.label.setFocus()
         
    def closeEvent(self, evt):
        self.closed.emit()
       
        QtWidgets.QWidget.closeEvent(self, evt)
       
    def changeColor(self, index):
        """Changes a box color"""
        l = self.colBox.itemText(index)
        color = self.colors[index]
        self.colBox.setStyleSheet("background-color: %s;" % rgb2hex(color))
        
        if l != "":
            self.label.setText(l)
        
    def boldT(self):
        """Toggles bold"""
        if self.boldv == False:
            self.boldb.setStyleSheet("font: bold; background-color: #787878;")
            self.boldv = True
        else:
            self.boldb.setStyleSheet("font: bold; background-color: ;")
            self.boldv = False
        
    def italicT(self):
        """Toggles italic"""
        if self.italicv == False:
            self.italicb.setStyleSheet("font: italic; background-color: #787878;")
            self.italicv = True
        else:
            self.italicb.setStyleSheet("font: italic; background-color: ;")
            self.italicv = False 
                
    def makeBackdrop(self):               
        """Makes a new backdrop"""
        self.close()
        p = self.data['padding']
        txt = self.label.text()
        f = "<" + (self.format.currentText()) + ">"
        idx = self.colBox.currentIndex()
        color = self.colors[idx]
        color = rgb2interface(color)
        if self.boldv == True:
            b = "<b>"
        else:
            b = ""
        if self.italicv == True:
            i = "<i>"
        else:
            i = ""

        selectedNodes = nuke.selectedNodes()
       
        # Get grid size
        gridWidth = nuke.toNode("preferences")['GridWidth'].getValue()
        gridHeight = nuke.toNode("preferences")['GridWidth'].getValue()
        
        nuke.Undo.begin()
        
        if len(selectedNodes) > 0 :
            # Calculate bounds for the backdrop node.
            bdX = min([node.xpos() for node in selectedNodes])
            bdY = min([node.ypos() for node in selectedNodes])
            bdW = max([node.xpos() + node.screenWidth() for node in selectedNodes])
            bdH = max([node.ypos() + node.screenHeight() for node in selectedNodes])
           
            # Get max Screen Width
            maxScreenW = max ([n.screenWidth() for n in selectedNodes])
           
            # Adjust Bounds
            bdX = int(bdX - p)
            bdY = int(bdY - (p + 60))
            bdW = int(bdW + p)
            bdH = int(bdH + p)
           
            # Create Backdrop
            n = nuke.nodes.BackdropNode(xpos = bdX, bdwidth = bdW - bdX, ypos = bdY, bdheight = bdH - bdY, label = f + b + i + txt, z_order = self.zorder.value(), tile_color = color, bookmark = self.bm.isChecked(), note_font = self.font.currentText(), note_font_size = self.fsize.value(), selected = True)
            if nuke_ver >= 12:     
               n['appearance'].setValue(self.style_drop.currentText())
               n['border_width'].setValue(self.w.value())            
           
        else:
            n = nuke.createNode('BackdropNode', inpanel = False)
            n['label'].setValue(f + b + i + txt)
            n['z_order'].setValue(self.zorder.value())
            n['tile_color'].setValue(color)
            n['bookmark'].setValue(self.bm.isChecked())
            n['note_font'].setValue(self.font.currentText())
            n['note_font_size'].setValue(self.fsize.value())
            if nuke_ver >= 12:     
               n['appearance'].setValue(self.style_drop.currentText())
               n['border_width'].setValue(self.w.value())
                
        # Add button to snap to selected
        k = n.knob('label')
        n.addKnob(k)
        k = n.knob('z_order')
        n.addKnob(k)
        for knob in n.knobs():
            if n.knob(knob).name() == "User":
                knob.setName("Backdrop Settings")
                knob.setLabel("backdrop_settings")
        
        nuke.Undo.end()
        
        try:
            for k in n.knobs():
                if 'padding' in k.name():
                    nuke.Undo.end()
                    return
                else:
                    padding = nuke.Int_Knob('padding', 'Padding')
                    n.addKnob(padding)
                    padding.setValue(p)
                    
                if 'snap' in k.name():
                    nuke.Undo.end()
                    return
                else: 
                    button = nuke.PyScript_Knob('snap','Snap to selected nodes')
                    button.setValue("this = nuke.thisNode()\nselNodes = nuke.selectedNodes()\npadding = this.knob('padding').value()\nif len(selNodes)== 0:\n\tpass\nelse:\n\tbdX = min([node.xpos() for node in selNodes]) - padding\n\tbdY = min([node.ypos() for node in selNodes]) - padding - 60\n\tbdW = max([node.xpos() + node.screenWidth() for node in selNodes]) + padding\n\tbdH = max([node.ypos() + node.screenHeight() for node in selNodes]) + padding\n\tthis.knob('xpos').setValue(bdX)\n\tthis.knob('ypos').setValue(bdY)\n\tthis.knob('bdwidth').setValue(bdW-bdX)\n\tthis.knob('bdheight').setValue(bdH-bdY)")
                    n.addKnob(button)
        except: pass

    def enableL(self):
        """Enables/disables the label button"""
        if self.labelt.isChecked():
            self.label.setEnabled(True)
        else:  
            self.label.setEnabled(False)
            
    def enableZ(self):
        """Enables/disables the z order button"""
        if self.zt.isChecked():
            self.zorder.setEnabled(True)
        else:  
            self.zorder.setEnabled(False)
        
    def editBackdrop(self):   
        """Edits selected backdrops"""                     
        self.close()
        txt = self.label.text()
        z = self.zorder.value()
        f = "<" + self.format.currentText() + ">"
        color = self.colBox.currentText()
        color = hex2interface(color)

        if self.boldv == True:
            b = "<b>"
        else:
            b = ""
        if self.italicv == True:
            i = "<i>"
        else:
            i = ""
            
        active_dag = get_current_dag()
        dag_node = None
        if active_dag:
            node = get_dag_node(active_dag)
            with node:            
                for n in nuke.selectedNodes():
                    if self.labelt.isChecked():
                        n['label'].setValue(f + b + i + txt)
                    if self.zt.isChecked():
                        n['z_order'].setValue(z)
                    n['tile_color'].setValue(color)
                    n['bookmark'].setValue(self.bm.isChecked())
                    n['note_font'].setValue(self.font.currentText())
                    n['note_font_size'].setValue(self.fsize.value()) 
                    if nuke_ver >= 12:
                       n['appearance'].setValue(self.style_drop.currentText())
                       n['border_width'].setValue(self.w.value())
                            
    def switch(self):
        """This is run when the edit button in the panel is pressed. Sets up the widget to edit mode"""
        
        active_dag = get_current_dag()
        dag_node = None
        if active_dag:
            node = get_dag_node(active_dag)
            with node:
                sel = nuke.selectedNodes()
                for n in sel:
                    n.setSelected(False)
                    if n.Class() == 'BackdropNode':
                        n.setSelected(True)
                        
                    sel_l = len(sel)   
                    
                    if sel_l == 1:
                        n = nuke.selectedNode()
                        lbl = n['label'].value()
                        col = n['tile_color'].value()
                   
                self.setWindowTitle("Edit backdrop")
                self.buttonBox.accepted.disconnect()
                self.buttonBox.accepted.connect(self.editBackdrop)
                
                if sel_l > 1:                
                    self.labelt.setVisible(True)
                    self.box6.setContentsMargins(16,0,0,0)  
                    self.zt.setVisible(True)
                    self.box5.setContentsMargins(0,0,0,0)  
                    
                elif sel_l == 1:
                    if "<center>" in lbl:
                        setCurrentText(self.format, "center")
                    else:
                        setCurrentText(self.format, "left")
                        
                    if "<b>" in lbl:
                        self.boldv = True
                        self.boldb.setStyleSheet("font: bold; background-color: #787878;")
                    else:
                        self.boldv = False
                        self.boldb.setStyleSheet("font: bold; background-color: ;")
                        
                    if "<i>" in lbl:
                        self.italicv = True
                        self.italicb.setStyleSheet("font: italic; background-color: #787878;")
                    else:
                        self.italicv = False
                        self.italicb.setStyleSheet("font: italic; background-color: ;")                
                        
                    col = interface2rgb(col)
                    col = rgb2hex(col)
        
                    lbl = lbl.split(">")[-1]
                    
                    if self.colBox.findText(col) == -1:
                        self.colBox.addItem(col)
                        model = self.colBox.model()
                        row = len(self.data['colors'])
                        model.setData(model.index(row, 0), QtGui.QColor(col), QtCore.Qt.BackgroundRole)
                        
                    setCurrentText(self.colBox, col)
                    self.colBox.setStyleSheet("background-color: %s;" % col)
                    self.label.setText(lbl)
                    self.zorder.setValue(n['z_order'].value())
                    setCurrentText(self.style_drop, n['appearance'].value())
                    self.w.setValue(n['border_width'].value())
                    self.bm.setChecked(n['bookmark'].value())
                    setCurrentText(self.font, n['note_font'].value())
                    self.fsize.setValue(n['note_font_size'].value())
                else:
                    self.zorder.setValue(self.data['zorder'])
        
_sew_instanceUI = None
   
def guiUI():

    load_settings()
   
    global _sew_instanceUI

    if _sew_instanceUI is not None:
        # Already an instance (make it really obvious - focused, in front and under cursor, like other Nuke GUI windows)
        _sew_instanceUI.show()
        _sew_instanceUI.activateWindow()
        _sew_instanceUI.raise_()
        return
   
    # Make a new instance, keeping it in a global variable to avoid multiple instances being opened
    _sew_instanceUI = BackdropManagerUI()

    def when_closedUI():
        global _sew_instanceUI
        _sew_instanceUI = None

    _sew_instanceUI.closed.connect(when_closedUI)

    modal = False
    if modal:
        _sew_instanceUI.exec_()
    else:
        _sew_instanceUI.show()
        
class BackdropPanel(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self) 
        
        self.b = BackdropManagerUI(self)
        
        self.setAcceptDrops(True)
        
        # Load settings from disc, and into Nuke
        self.settings = Overrides()
        self.d = self.settings.restore()

        # Stack widgets atop each other
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
        # Add box for buttons
        gbox = QtWidgets.QHBoxLayout()
        gbox.setContentsMargins(30,0,30,0)
        gbox.setSpacing(5)
        self.layout.addLayout(gbox)
        
        # Buttons        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Backdrop.png"))
        btn.setToolTip("Make backdrop")                  
        btn.setFixedSize(40,25)       
        btn.clicked.connect(guiUI)
        gbox.addWidget(btn)
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Edit.png"))
        btn.setToolTip("Edit selected backdrops")                          
        btn.setFixedSize(40,25)
        btn.clicked.connect(guiEdit)
        gbox.addWidget(btn) 
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Toggle.png"))
        btn.setToolTip("Toggle fill/border mode on selected backdrops")
        btn.setFixedSize(40,25)        
        btn.clicked.connect(wrapped(self.toggle))
        gbox.addWidget(btn)        
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Selected.png"))
        btn.setToolTip("Set selected backdrops to default style")
        btn.setFixedSize(40,25)        
        btn.clicked.connect(wrapped(self.setStyleSel))
        gbox.addWidget(btn)
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "All.png"))
        btn.setToolTip("Set all backdrops to default style")
        btn.setFixedSize(40,25)
        btn.clicked.connect(wrapped(self.setStyle))
        gbox.addWidget(btn)    
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Snap.png"))
        btn.setToolTip("Snap backdrop size")
        btn.setFixedSize(40,25)
        btn.clicked.connect(wrapped(snap))
        gbox.addWidget(btn)                    
        
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtGui.QIcon(icon_path + "Settings.png"))
        btn.setToolTip("Open settings")
        btn.setFixedSize(40,25)
        btn.clicked.connect(gui)
        gbox.addWidget(btn)            
        
        # Make color boxes
        self.makeBoxes()   
        
    def get_data(self):
        """Re-order and save colors"""
        self.settings = Overrides()        
        d = self.settings.restore()      
        self.colors = []
        for n in range(self.box_layout.count()):
            # Get the widget at each index in turn.
            try:
                w = self.box_layout.itemAt(n).widget()
                self.colors.append(w.data)
            except: pass
        d['colors'] = self.colors

        self.settings.save()
        
    def dragEnterEvent(self, e):
        e.accept()
    
    ### TO DO: Add separate drop event allowing Nuke tile-colors to be dragged/dropped as new boxes
    def dropEvent(self, e):
        """Rearrange box widgets on drop"""
        pos = e.pos()
        widget = e.source()

        for n in range(self.box_layout.count()):
            # Get the widget at each index in turn.
            w = self.box_layout.itemAt(n).widget()
            drop_here = pos.x() <= w.x() + w.size().width() // 2

            if drop_here:
                # We didn't drag past this widget.
                # insert to the left of it.
                self.box_layout.insertWidget(n-1, widget)
                self.get_data()
                break

        e.accept()          
        
    def setStyleSel(self):
        """Set the selected backdrops to settings style"""
        self.d = self.settings.restore()
        
        f = "<" + self.d['align'] + ">"
        
        if self.d['bold'] == True:
            b = "<b>"
        else:
            b = ""
        if self.d['italic'] == True:
            i = "<i>"
        else:
            i = ""
        
        for n in nuke.selectedNodes():
            n.setSelected(False)
            if n.Class() == 'BackdropNode':
               n.setSelected(True)
               
        for n in nuke.selectedNodes():
            lbl = n['label'].value()
            lbl = lbl.split(">")[-1]
            n.knob('label').setValue(f + b + i + lbl)
            n.knob('note_font').setValue(self.d['font'])
            n.knob('note_font_size').setValue(self.d['font_size'])
            n.knob('appearance').setValue(self.d['style'])
            n.knob('border_width').setValue(self.d['width'])
            n.knob('bookmark').setValue(self.d['bookmark'])
            
    def setStyle(self):
        """Sets all backdrops to settings style"""
        self.d = self.settings.restore()
        
        f = "<" + self.d['align'] + ">"
        
        if self.d['bold'] == True:
            b = "<b>"
        else:
            b = ""
        if self.d['italic'] == True:
            i = "<i>"
        else:
            i = ""
        
        for n in nuke.allNodes():
            if n.Class() == 'BackdropNode':
                lbl = n['label'].value()
                lbl = lbl.split(">")[-1]
                n.knob('label').setValue(f + b + i + lbl)          
                n.knob('note_font').setValue(self.d['font'])
                n.knob('note_font_size').setValue(self.d['font_size'])
                n.knob('appearance').setValue(self.d['style'])
                n.knob('border_width').setValue(self.d['width'])
                n.knob('bookmark').setValue(self.d['bookmark'])        
                
    def makeBoxes(self):
        # Box group
        self.box_group = QtWidgets.QGroupBox()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(5)
        self.box_layout = QtWidgets.QHBoxLayout()
        self.box_layout.setSpacing(15)
        vbox.addLayout(self.box_layout)
        self.box_group.setLayout(vbox)

        self.layout.addWidget(self.box_group)
            
        # Get colors from file
        self.settings = Overrides()
        d = self.settings.restore()        
        self.colors = d['colors']

        # Make boxes
        for idx, color in enumerate(self.colors):
            btn = DragButton()
            btn.setToolTip("Recolor selected backdrops and sticky notes")            
            btn.setStyleSheet("background-color: %s;" % rgb2hex(color))            
            btn.set_data(color)
            btn.setFixedSize(20,20)
            self.box_layout.addWidget(btn)
            btn.clicked.connect(partial(wrapped(self.setColor), idx))
            
        # Make button Box
        self.box = QtWidgets.QHBoxLayout()
        self.box.setContentsMargins(0,10,0,0)
        self.box.setSpacing(10)
        self.box.addStretch(375)
        self.layout.addLayout(self.box) 
    
        # Make minus button
        minb = QtWidgets.QPushButton("-")
        minb.setToolTip("Remove last color.")
        minb.setFixedSize(20,20)
        minb.clicked.connect(self.min)
        self.box.addWidget(minb)
    
        # Make plus button
        addb = QtWidgets.QPushButton("+")
        addb.setToolTip("Add a new color.")
        addb.clicked.connect(self.add)
        addb.setFixedSize(20,20)        
        self.box.addWidget(addb)        
        
        # Make refresh button
        refresh = QtWidgets.QPushButton("Reload")
        refresh.setToolTip("Refresh color boxes")  
        refresh.setFixedSize(60,20)
        refresh.clicked.connect(self.clear)
        self.box.addWidget(refresh)
        
    def min(self):
        """Remove box"""
        idx = len(self.colors) - 1
        try:
            self.colors.pop(idx)
        except: pass
        self.settings.save()           

        self.clear()       

    def add(self):
        """Add a new color box"""
        col = nuke.getColor()
        if col:
            col = interface2rgb(col)
            
            idx = len(self.colors)
            self.colors.append(col)
            self.settings.save()         
    
            btn = DragButton()
            btn.setToolTip("Recolor selected backdrops and sticky notes")                       
            btn.set_data(col)
            btn.setFixedSize(20,20)
            btn.setStyleSheet("background-color: %s;" % rgb2hex(col))
    
            self.box_layout.addWidget(btn)

            btn.clicked.connect(partial(self.setColor, idx))
        
    def clear(self):
        # Delete box group widget and remake
        self.box_group.deleteLater()
        self.box.deleteLater()
        self.makeBoxes()
            
    def setColor(self, color_idx):
        # Get Selected Nodes
        color = self.colors[color_idx]
        color = int('%02x%02x%2x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255),1),16)

        for n in nuke.selectedNodes():
            n.setSelected(False)
            if n.Class() == 'StickyNote' or n.Class() == 'BackdropNode':
               n.setSelected(True)
               
        for n in nuke.selectedNodes():
            n.knob('tile_color').setValue(color)     
            
    def toggle(self):    
        """Toggles backdrops between border and fill"""  
        for n in nuke.selectedNodes():
            n.setSelected(False)
            if n.Class() == 'BackdropNode':
               n.setSelected(True)

        for n in nuke.selectedNodes():
            if n['appearance'].value() == 'Fill':
                n.knob('appearance').setValue('Border')
            else:
                n.knob('appearance').setValue('Fill')  
                
    def updateValue(self):
        ## Nuke "updateValue" fix        
        pass                  

_sew_instanceEdit = None   
           
def guiEdit():

    load_settings()
   
    global _sew_instanceEdit
   
    # Make a new instance, keeping it in a global variable to avoid multiple instances being opened

    if _sew_instanceEdit is not None:
        # Already an instance (make it really obvious - focused, in front and under cursor, like other Nuke GUI windows)
        _sew_instanceEdit.show()
        _sew_instanceEdit.activateWindow()
        _sew_instanceEdit.raise_()
        return
    
    def when_closedEdit():
        global _sew_instanceEdit
        _sew_instanceEdit = None
                
    for n in nuke.selectedNodes():
        n.setSelected(False)
        if n.Class() == 'BackdropNode':
            n.setSelected(True)    
            
    if len(nuke.selectedNodes()) >= 1:
        _sew_instanceEdit = BackdropManagerUI()
        _sew_instanceEdit.switch()
    
        _sew_instanceEdit.closed.connect(when_closedEdit)
    
        modal = False
        if modal:
            _sew_instanceEdit.exec_()
        else:
            _sew_instanceEdit.show()
             
def nuke_setup():
    """ Call this from menu.py to setup"""
    # Load settings
    settings = Overrides()
    d = settings.restore()

    # Menu item to open shortcut editor
    nuke.menu("Nuke").addCommand("Edit/Backdrop Manager Settings", gui)
    nuke.menu("Node Graph").addCommand("Create Backdrop", guiUI, d['shortcut'])
    nuke.menu("Node Graph").addCommand("Snap Backdrop", wrapped(snap), d['snap'])    
    panels.registerWidgetAsPanel('nuke.BP', 'Backdrop Manager', 'BackdropPanel')
    
    nuke.BP = BackdropPanel

if __name__ == "__main__":
    nuke_setup()
