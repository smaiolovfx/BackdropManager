"""Persistent settings for BackdropManager."""

import json
import os
import traceback

import nuke

from .paths import PACKAGE_DIR

SETTINGS_VERSION = 3
SETTINGS_FILENAME = "backdropmanager_settings.json"


def _load_json(path):
    try:
        if not os.path.isfile(path):
            return None
        with open(path) as stream:
            return json.load(stream)
    except Exception:
        print("Error loading %r" % path)
        traceback.print_exc()
        return None


def _save_json(obj, path):
    try:
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
    except Exception:
        print("Error saving BackdropManager settings")
        traceback.print_exc()


def _merge_loaded(loaded, defaults):
    """Merge a loaded settings file onto defaults.

    Returns updated dict, or None if loaded is unusable (caller keeps defaults).
    """
    try:
        version = int(loaded["version"])
        payload = loaded["settings"]
        if version < 2 or not isinstance(payload, dict):
            return None
        merged = dict(defaults)
        merged.update(payload)
        return merged
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


class Overrides(object):
    """Load, save, and reset user preferences."""

    def __init__(self):
        nuke_dir = os.path.expanduser("~/.nuke/")
        if nuke_dir in PACKAGE_DIR:
            self.settings_path = os.path.join(PACKAGE_DIR, SETTINGS_FILENAME)
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
        """Load settings from disk. Always returns a complete defaults dict.

        Missing file → write defaults (first run).
        Corrupt / wrong shape / old version → keep in-memory defaults, leave file alone.
        Partial settings → merge onto defaults (missing keys stay default).
        """
        settings = _load_json(path=self.settings_path)
        self.defaults = self.default_settings()

        if settings is None:
            if not os.path.isfile(self.settings_path):
                self.clear()
            else:
                nuke.warning(
                    "BackdropManager settings at %r could not be read; using defaults."
                    % self.settings_path
                )
            return self.defaults

        merged = _merge_loaded(settings, self.defaults)
        if merged is None:
            nuke.warning(
                "BackdropManager settings at %r are invalid or outdated "
                "(need version >= 2); using defaults."
                % self.settings_path
            )
            return self.defaults

        self.defaults = merged
        return self.defaults
