def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    elif len(hex_color) != 6:
        raise ValueError("Invalid hex color format. Must be 3 or 6 digits.")

    try:
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise ValueError("Invalid hex color value.") from exc


def get_luminance(r, g, b):
    r_srgb = r / 255.0
    g_srgb = g / 255.0
    b_srgb = b / 255.0

    def linearize_channel(channel):
        if channel <= 0.03928:
            return channel / 12.92
        else:
            return ((channel + 0.055) / 1.055) ** 2.4

    r_linear = linearize_channel(r_srgb)
    g_linear = linearize_channel(g_srgb)
    b_linear = linearize_channel(b_srgb)

    luminance = (0.2126 * r_linear) + (0.7152 * g_linear) + (0.0722 * b_linear)
    return luminance


def get_contrast_ratio(hex_color1, hex_color2):
    try:
        rgb1 = hex_to_rgb(hex_color1)
        rgb2 = hex_to_rgb(hex_color2)
    except ValueError as e:
        return f"Error: {e}"

    l1 = get_luminance(rgb1[0], rgb1[1], rgb1[2])
    l2 = get_luminance(rgb2[0], rgb2[1], rgb2[2])

    if l1 < l2:
        l1, l2 = l2, l1

    contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
    return round(contrast_ratio, 2)


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
