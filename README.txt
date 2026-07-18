"""
A backdrop manager for Nuke's backdrops.
Parts based on shortcuteditor by Ben Dickson.

Requires Nuke 11 or later (PySide2 / PySide6).

This tool adds settings in Nuke under /Edit/Backdrop Manager Settings, and a panel for ease of use under Windows/Custom/Backdrop Manager.

To use, copy or symlink ``src/BackdropManager`` into your ``~/.nuke/`` directory
(so you have ``~/.nuke/BackdropManager/``). Icons ship inside the package.

In ~/.nuke/menu.py add this:
import BackdropManager

Feel free to contact me if you have any questions or suggestions for how BackdropManager can be improved:
Samantha Maiolo - samanthamaiolovfx@gmail.com
"""
