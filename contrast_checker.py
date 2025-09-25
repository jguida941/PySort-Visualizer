import math


def _linearize_channel(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return math.pow((channel + 0.055) / 1.055, 2.4)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    parsed = hex_color.lstrip("#")
    if len(parsed) == 3:
        parsed = "".join(c * 2 for c in parsed)
    elif len(parsed) != 6:
        raise ValueError("Invalid hex color format. Must be 3 or 6 digits.")

    try:
        r = int(parsed[0:2], 16)
        g = int(parsed[2:4], 16)
        b = int(parsed[4:6], 16)
        return r, g, b
    except ValueError as exc:
        raise ValueError("Invalid hex color value.") from exc


def get_luminance(r: int, g: int, b: int) -> float:
    r_srgb = r / 255.0
    g_srgb = g / 255.0
    b_srgb = b / 255.0

    r_linear = _linearize_channel(r_srgb)
    g_linear = _linearize_channel(g_srgb)
    b_linear = _linearize_channel(b_srgb)

    return (0.2126 * r_linear) + (0.7152 * g_linear) + (0.0722 * b_linear)


def get_contrast_ratio(hex_color1: str, hex_color2: str) -> float:
    rgb1 = hex_to_rgb(hex_color1)
    rgb2 = hex_to_rgb(hex_color2)

    l1 = get_luminance(*rgb1)
    l2 = get_luminance(*rgb2)

    if l1 < l2:
        l1, l2 = l2, l1

    contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
    return math.floor(contrast_ratio * 100 + 0.5) / 100


if __name__ == "__main__":
    bg_color = "#0f1115"
    caption_color = "#aeb6c2"
    hud_color = "#e6e6e6"

    print(f"Checking contrast between caption color ({caption_color}) and background ({bg_color}):")
    ratio = get_contrast_ratio(caption_color, bg_color)
    print(f"  Contrast Ratio: {ratio}:1")

    print(f"Checking contrast between HUD color ({hud_color}) and background ({bg_color}):")
    ratio = get_contrast_ratio(hud_color, bg_color)
    print(f"  Contrast Ratio: {ratio}:1")
