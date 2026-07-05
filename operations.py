"""Backdrop commands that operate on the current Nuke script."""

import nuke

from .settings import Overrides


def backdrop_areas(nodes):
    """Return selected backdrop areas and their source nodes."""
    backdrop_dict = {}
    areas = []
    for node in nodes:
        if node.Class() == "BackdropNode":
            backdrop_area = int(node["bdwidth"].value() * node["bdheight"].value())
            backdrop_dict[node] = backdrop_area
            areas.append(backdrop_area)
            areas.sort()
    return areas, backdrop_dict


def snap():
    """Snap the largest selected backdrop to the other selected nodes."""
    settings = Overrides()
    data = settings.restore()
    selected_nodes = nuke.selectedNodes()
    padding = data["padding"]

    if len(selected_nodes) == 0:
        return

    areas, backdrop_dict = backdrop_areas(selected_nodes)
    if areas == []:
        return

    largest = [node for node, area in backdrop_dict.items() if area == areas[-1]][0]
    selected_nodes.remove(largest)
    if not selected_nodes:
        return

    bd_x = min([node.xpos() for node in selected_nodes]) - padding
    bd_y = min([node.ypos() for node in selected_nodes]) - padding - 60
    bd_w = max([node.xpos() + node.screenWidth() for node in selected_nodes]) + padding
    bd_h = max([node.ypos() + node.screenHeight() for node in selected_nodes]) + padding

    largest.knob("bdwidth").setValue(bd_w - bd_x)
    largest.knob("xpos").setValue(bd_x)
    largest.knob("bdheight").setValue(bd_h - bd_y)
    largest.knob("ypos").setValue(bd_y)
