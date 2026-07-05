"""Color conversion helpers for Nuke and Qt UI values."""

def interface_to_rgb(hex_value, normalize=True):
    """Convert a Nuke interface 32-bit color value to normalized RGB values."""
    return [(0xFF & hex_value >> i) / 255.0 for i in [24, 16, 8]]


def rgb_to_hex(rgba_values):
    """Convert normalized RGB values to a hex color string."""
    rgba_values = [int(i * 255) for i in rgba_values]
    if len(rgba_values) < 3:
        return None
    return "#%02x%02x%02x" % (rgba_values[0], rgba_values[1], rgba_values[2])


def hex_to_rgb(hex_color):
    """Convert a hex color string to RGB values."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def hex_to_interface(hex_color):
    """Convert a hex color string to a Nuke interface 32-bit color value."""
    hex_color = hex_color.lstrip("#")
    return int(hex_color + "00", 16)


def rgb_to_interface(rgb):
    """Convert normalized RGB values to a Nuke interface 32-bit color value."""
    return int(
    "%02x%02x%02x%02x"
    % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 1),
    16,
    )