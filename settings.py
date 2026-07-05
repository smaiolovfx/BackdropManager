"""Persistent settings for BackdropManager."""

import json
import os
import traceback

import nuke

from .paths import PROJECT_ROOT

SETTINGS_VERSION = 3
SETTINGS_FILENAME = "backdropmanager_settings.json"


def _load_json(path):
    def _load_internal():
        if not os.path.isfile(path):
            print("Settings file %r does not exist" % (path))
            return None
        with open(path) as stream:
            return json.load(stream)

    try:
        return _load_internal()
    except Exception:
        print("Error loading %r" % path)
        traceback.print_exc()
        return None


def _save_json(obj, path):
    def _save_internal():
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as error:
                if error.errno != 17:
                    raise

        with open(path, "w") as stream:
            json.dump(obj, fp=stream, sort_keys=True, indent=1, separators=(",", ": "))
            stream.write("\n")

    try:
        _save_internal()
    except Exception:
        print("Error saving BackdropManager settings")
        traceback.print_exc()


def load_settings():
    """Load settings from disk."""
    settings = Overrides()
    settings.restore()
    return settings


class Overrides(object):
    """Load, save, and reset user preferences."""

    def __init__(self):
        nuke_dir = os.path.expanduser("~/.nuke/")
        if nuke_dir in PROJECT_ROOT:
            self.settings_path = os.path.join(PROJECT_ROOT, SETTINGS_FILENAME)
        else:
            self.settings_path = os.path.join(nuke_dir, SETTINGS_FILENAME)
        self.defaults = self.default_settings()

    def default_settings(self):
        return {
            "colors": [
                (0.26, 0.26, 0.26),
                (0.32, 0.255, 0.19),
                (0.32, 0.19, 0.19),
                (0.32, 0.19, 0.255),
                (0.255, 0.19, 0.32),
                (0.19, 0.19, 0.32),
                (0.19, 0.255, 0.32),
                (0.19, 0.32, 0.19),
            ],
            "labels": ["", "", "", "", "", "", "", ""],
            "shortcut": "CTRL+B",
            "snap": "CTRL+SHIFT+B",
            "padding": 40,
            "style": "Fill",
            "width": 15,
            "zorder": 0,
            "bookmark": 1,
            "font": "Source Code Pro Light",
            "font_size": 40,
            "bold": False,
            "italic": False,
            "align": "center",
        }

    def save(self):
        settings = {"settings": self.defaults, "version": SETTINGS_VERSION}
        _save_json(obj=settings, path=self.settings_path)

    def clear(self):
        self.defaults = self.default_settings()
        self.save()

    def restore(self):
        settings = _load_json(path=self.settings_path)
        self.defaults = self.default_settings()

        if settings is None:
            self.clear()
            return self.defaults

        if int(settings["version"]) >= 2:
            self.defaults.update(settings["settings"])
            return self.defaults

        nuke.warning(
            "Wrong version of backdrop manager config, nothing loaded "
            "(version %s loaded, version %s is the latest), path was %r. "
            "Please either delete your settings file or re-download the latest "
            "BackdropManager."
            % (int(settings["version"]), SETTINGS_VERSION, self.settings_path)
        )
        return self.defaults

    def load(self):
        return {"settings": self.defaults, "version": SETTINGS_VERSION}
