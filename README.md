# BackdropManager

A backdrop toolkit for [Foundry Nuke](https://www.foundry.com/products/nuke). It lets you create, edit, recolor and resize Backdrop nodes from a dockable panel and keyboard shortcuts, with your own color presets and default styles.

Requires **Nuke 11 or later** (PySide2 or PySide6).

## Features

- **Make backdrop** (`Ctrl+B`): wraps the selected nodes in a backdrop. A dialog lets you set the color, label, font, alignment, appearance, bookmark and Z order before it's created.
- **Edit backdrops**: change the same properties on one or more selected backdrops at once.
- **Snap backdrop** (`Ctrl+Shift+B`): resizes the largest selected backdrop to fit the other selected nodes, with configurable padding. Each backdrop also gets a *Snap to selected nodes* button on its own properties panel.
- **Color presets**: one-click recoloring of selected backdrops and sticky notes. Add, remove and drag to reorder presets in the panel.
- **Fill/Border toggle**: switch the appearance of selected backdrops.
- **Apply default style**: reset selected backdrops, or every backdrop in the script, to your saved defaults.
- **Works inside Groups**: create and edit operations stay pinned to the Node Graph they were started from.

## Installation

1. Copy or symlink this repository into your `.nuke` directory, so the folder is named `~/.nuke/BackdropManager/`:

   ```bash
   git clone https://github.com/smaiolovfx/BackdropManager.git ~/.nuke/BackdropManager
   ```

2. Add this line to `~/.nuke/menu.py` (create the file if it doesn't exist):

   ```python
   import BackdropManager
   ```

3. Restart Nuke. The script editor prints the BackdropManager version on startup.

## Usage

| Where | What |
| --- | --- |
| **Windows → Custom → Backdrop Manager** | Dockable panel with the toolbar and color presets |
| **Edit → Backdrop Manager Settings** | Default shortcuts, padding, font, style and color presets |
| **Node Graph → Create Backdrop** | Make backdrop (default `Ctrl+B`) |
| **Node Graph → Snap Backdrop** | Snap backdrop (default `Ctrl+Shift+B`) |

### Panel toolbar

| Icon | Action |
| --- | --- |
| ![](icons/Backdrop.png) | Make backdrop |
| ![](icons/Edit.png) | Edit selected backdrops |
| ![](icons/Toggle.png) | Toggle fill/border on selected backdrops |
| ![](icons/Selected.png) | Apply default style to selected backdrops |
| ![](icons/All.png) | Apply default style to all backdrops |
| ![](icons/Snap.png) | Snap backdrop size |
| ![](icons/Settings.png) | Open settings |

## Settings

Settings are saved to `backdropmanager_settings.json`. It is created on first run inside the package folder when the package is installed under `~/.nuke/`, and directly in `~/.nuke/` otherwise. To start over, click **Set to default** in the settings dialog or delete the file.

## Credits

Created by Samantha Maiolo. Parts are based on [shortcuteditor](https://github.com/dbr/shortcuteditor-nuke) by Ben Dickson.

Questions or suggestions: samanthamaiolovfx@gmail.com
