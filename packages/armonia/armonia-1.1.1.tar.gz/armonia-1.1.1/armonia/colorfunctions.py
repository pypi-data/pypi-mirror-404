"""Common color transformation functions for use with Theme computed colors.

This module provides a collection of common color transformation functions
that can be used to create computed colors in themes. All functions return
a callable that takes a Theme instance and returns an HSLColor.

Example usage::

    theme = Theme()
    theme.set_color("primary", HSLColor.from_hex("#3498db"))

    # Create computed colors using transformation functions
    theme.set_computed_color("primary_light", lighter("primary", 0.2))
    theme.set_computed_color("primary_dark", darker("primary", 0.2))
    theme.set_computed_color("primary_muted", muted("primary", 0.3))
"""

from collections.abc import Callable

from polychromos.color import HSLColor
from polychromos.palette import Palette

from armonia.theme import ComputeColorFn, Theme


def lighter(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Create a lighter version of a color by increasing its lightness.

    :param color_key: The key of the color to lighten.
    :type color_key: str
    :param amount: The amount to increase lightness (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the lighter color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.delta(0, 0, amount)

    return compute


def darker(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Create a darker version of a color by decreasing its lightness.

    :param color_key: The key of the color to darken.
    :type color_key: str
    :param amount: The amount to decrease lightness (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the darker color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.delta(0, 0, -amount)

    return compute


def saturate(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Increase the saturation of a color, making it more vivid.

    :param color_key: The key of the color to saturate.
    :type color_key: str
    :param amount: The amount to increase saturation (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the saturated color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.delta(0, amount, 0)

    return compute


def desaturate(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Decrease the saturation of a color, making it more gray.

    :param color_key: The key of the color to desaturate.
    :type color_key: str
    :param amount: The amount to decrease saturation (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the desaturated color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.delta(0, -amount, 0)

    return compute


def muted(color_key: str, amount: float = 0.3) -> ComputeColorFn:
    """
    Create a muted version of a color by significantly reducing its saturation.

    This is a convenience function that desaturates more than the default.

    :param color_key: The key of the color to mute.
    :type color_key: str
    :param amount: The amount to decrease saturation (0.0 to 1.0). Defaults to 0.3.
    :type amount: float
    :return: A function that computes the muted color.
    :rtype: ComputeColorFn
    """
    return desaturate(color_key, amount)


def brighten(color_key: str, amount: float = 0.2) -> ComputeColorFn:
    """
    Make a color significantly brighter by increasing its lightness.

    This is a convenience function that lightens more than the default.

    :param color_key: The key of the color to brighten.
    :type color_key: str
    :param amount: The amount to increase lightness (0.0 to 1.0). Defaults to 0.2.
    :type amount: float
    :return: A function that computes the brightened color.
    :rtype: ComputeColorFn
    """
    return lighter(color_key, amount)


def dim(color_key: str, amount: float = 0.2) -> ComputeColorFn:
    """
    Make a color significantly darker by decreasing its lightness.

    This is a convenience function that darkens more than the default.

    :param color_key: The key of the color to dim.
    :type color_key: str
    :param amount: The amount to decrease lightness (0.0 to 1.0). Defaults to 0.2.
    :type amount: float
    :return: A function that computes the dimmed color.
    :rtype: ComputeColorFn
    """
    return darker(color_key, amount)


def rotate_hue(color_key: str, degrees: float) -> ComputeColorFn:
    """
    Rotate the hue of a color by a specified amount.

    :param color_key: The key of the color to rotate.
    :type color_key: str
    :param degrees: The degrees to rotate the hue (0-360). Can be negative.
    :type degrees: float
    :return: A function that computes the hue-rotated color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        hue_delta = (degrees % 360) / 360.0
        return color.delta(hue_delta, 0, 0)

    return compute


def adjust(
    color_key: str,
    hue_delta: float = 0.0,
    saturation_delta: float = 0.0,
    lightness_delta: float = 0.0,
    opacity_delta: float = 0.0,
) -> ComputeColorFn:
    """
    Create an adjusted version of a color by shifting multiple components.

    This is a general-purpose function that allows fine-tuning of all color components.

    :param color_key: The key of the color to adjust.
    :type color_key: str
    :param hue_delta: The amount to shift hue (0.0 to 1.0). Defaults to 0.0.
    :type hue_delta: float
    :param saturation_delta: The amount to shift saturation. Defaults to 0.0.
    :type saturation_delta: float
    :param lightness_delta: The amount to shift lightness. Defaults to 0.0.
    :type lightness_delta: float
    :param opacity_delta: The amount to shift opacity. Defaults to 0.0.
    :type opacity_delta: float
    :return: A function that computes the adjusted color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.delta(hue_delta, saturation_delta, lightness_delta, opacity_delta)

    return compute


def alpha(color_key: str, opacity: float) -> ComputeColorFn:
    """
    Set the opacity/alpha channel of a color.

    :param color_key: The key of the color to modify.
    :type color_key: str
    :param opacity: The opacity value (0.0 to 1.0, where 1.0 is fully opaque).
    :type opacity: float
    :return: A function that computes the color with adjusted opacity.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        opacity_delta = opacity - color.opacity
        return color.delta(0, 0, 0, opacity_delta)

    return compute


def mix(color_key1: str, color_key2: str, weight: float = 0.5) -> ComputeColorFn:
    """
    Mix two colors together using linear interpolation.

    :param color_key1: The key of the first color.
    :type color_key1: str
    :param color_key2: The key of the second color.
    :type color_key2: str
    :param weight: The weight of the second color (0.0 to 1.0). Defaults to 0.5.
    :type weight: float
    :return: A function that computes the mixed color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color1 = theme.get_color(color_key1)
        color2 = theme.get_color(color_key2)
        return Palette.lerp(color1, color2, weight)

    return compute


def softer(color_key: str, background_key: str, amount: float = 0.3) -> ComputeColorFn:
    """
    Make a color softer by shifting it towards a background color.

    This is useful for creating subtle variations that blend better with a background.

    :param color_key: The key of the color to soften.
    :type color_key: str
    :param background_key: The key of the background color to shift towards.
    :type background_key: str
    :param amount: How much to shift towards the background (0.0 to 1.0). Defaults to 0.3.
    :type amount: float
    :return: A function that computes the softer color.
    :rtype: ComputeColorFn
    """
    return mix(color_key, background_key, amount)


def stronger(color_key: str, background_key: str, amount: float = 0.3) -> ComputeColorFn:
    """
    Make a color stronger by shifting it away from a background color.

    This creates more contrast with the background by mixing with the complementary
    color direction.

    :param color_key: The key of the color to strengthen.
    :type color_key: str
    :param background_key: The key of the background color to shift away from.
    :type background_key: str
    :param amount: How much to shift away from the background (0.0 to 1.0). Defaults to 0.3.
    :type amount: float
    :return: A function that computes the stronger color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        background = theme.get_color(background_key)

        saturation_delta = amount if color.saturation < 0.8 else 0
        lightness_delta = amount if background.lightness > 0.5 else -amount

        return color.delta(0, saturation_delta, lightness_delta)

    return compute


def complementary(
    color_key: str, mute_saturation: float = 0.0, mute_lightness: float = 0.0
) -> ComputeColorFn:
    """
    Get the complementary color (opposite on the color wheel).

    :param color_key: The key of the color to get the complement of.
    :type color_key: str
    :param mute_saturation: How much to decrease the saturation (0.0 to 1.0). Defaults to 0.0.
    :type mute_saturation: float
    :param mute_lightness: How much to decrease the lightness (0.0 to 1.0). Defaults to 0.0.
    :type mute_lightness: float
    :return: A function that computes the complementary color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return Palette.complementary(color, mute_saturation, mute_lightness)

    return compute


def grayscale(color_key: str) -> ComputeColorFn:
    """
    Convert a color to grayscale by removing all saturation.

    :param color_key: The key of the color to convert to grayscale.
    :type color_key: str
    :return: A function that computes the grayscale color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return HSLColor(color.hue, 0.0, color.lightness, color.opacity)

    return compute


def invert(color_key: str) -> ComputeColorFn:
    """
    Invert a color by inverting its lightness.

    :param color_key: The key of the color to invert.
    :type color_key: str
    :return: A function that computes the inverted color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.invert_lightness()

    return compute


def fade(color_key: str, opacity: float) -> ComputeColorFn:
    """
    Set the opacity of a color (alias for alpha).

    :param color_key: The key of the color to fade.
    :type color_key: str
    :param opacity: The opacity value (0.0 to 1.0).
    :type opacity: float
    :return: A function that computes the faded color.
    :rtype: ComputeColorFn
    """
    return alpha(color_key, opacity)


def tint(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Mix a color with white to create a tint.

    :param color_key: The key of the color to tint.
    :type color_key: str
    :param amount: The amount of white to mix in (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the tinted color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        white = HSLColor(0, 0, 1.0, 1.0)
        return Palette.lerp(color, white, amount)

    return compute


def shade(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Mix a color with black to create a shade.

    :param color_key: The key of the color to shade.
    :type color_key: str
    :param amount: The amount of black to mix in (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the shaded color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        black = HSLColor(0, 0, 0.0, 1.0)
        return Palette.lerp(color, black, amount)

    return compute


def tone(color_key: str, amount: float = 0.1) -> ComputeColorFn:
    """
    Mix a color with gray to create a tone.

    :param color_key: The key of the color to tone.
    :type color_key: str
    :param amount: The amount of gray to mix in (0.0 to 1.0). Defaults to 0.1.
    :type amount: float
    :return: A function that computes the toned color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        gray = HSLColor(0, 0, 0.5, 1.0)
        return Palette.lerp(color, gray, amount)

    return compute


def contrast(
    color_key: str, light_color_key: str = "white", dark_color_key: str = "black"
) -> ComputeColorFn:
    """
    Choose a contrasting color (light or dark) based on perceptual color distance.

    This is useful for determining text color on a colored background.
    Uses polychromos' pick_contrasting_color which provides better contrast detection
    than simple lightness thresholds.

    :param color_key: The key of the color to check.
    :type color_key: str
    :param light_color_key: The key of the light color to use. Defaults to "white".
    :type light_color_key: str
    :param dark_color_key: The key of the dark color to use. Defaults to "black".
    :type dark_color_key: str
    :return: A function that computes the contrasting color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        light_color = theme.get_color(light_color_key)
        dark_color = theme.get_color(dark_color_key)
        return color.pick_contrasting_color(dark_color, light_color, method="auto")

    return compute


def alias(color_key: str) -> ComputeColorFn:
    """
    Create an alias to another color.

    This allows referencing the same color with different names.

    :param color_key: The key of the color to alias.
    :type color_key: str
    :return: A function that returns the aliased color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        return theme.get_color(color_key)

    return compute


def multi(color_key: str, *transforms: Callable[[HSLColor], HSLColor]) -> ComputeColorFn:
    """
    Apply multiple color transformations sequentially.

    Each transformation is a function that takes an HSLColor and returns an HSLColor.
    Transformations are applied in order, with each operating on the result of the previous.

    Example::

        # Create a color that is lighter, then desaturated
        theme.set_computed_color("subtle", multi(
            "primary",
            lambda c: c.delta(0, 0, 0.2),      # lighter
            lambda c: c.delta(0, -0.3, 0)      # desaturate
        ))

    :param color_key: The key of the base color to transform.
    :type color_key: str
    :param transforms: Variable number of transformation functions that take and return HSLColor.
    :type transforms: Callable[[HSLColor], HSLColor]
    :return: A function that applies all transformations sequentially.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        result = theme.get_color(color_key)
        for transform in transforms:
            result = transform(result)
        return result

    return compute


def scale_saturation(color_key: str, factor: float) -> ComputeColorFn:
    """
    Scale the saturation of a color using multiplication (multiply mode).

    Formula: new_saturation = saturation * factor

    :param color_key: The key of the color to scale.
    :type color_key: str
    :param factor: The scaling factor (0.0 to 2.0+). Values < 1.0 decrease saturation,
                   values > 1.0 increase it.
    :type factor: float
    :return: A function that computes the scaled color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.multiply_components(factor, 1.0)

    return compute


def scale_lightness(color_key: str, factor: float) -> ComputeColorFn:
    """
    Scale the lightness of a color using multiplication (multiply mode).

    Formula: new_lightness = lightness * factor

    :param color_key: The key of the color to scale.
    :type color_key: str
    :param factor: The scaling factor (0.0 to 2.0+). Values < 1.0 darken,
                   values > 1.0 lighten.
    :type factor: float
    :return: A function that computes the scaled color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        return color.multiply_components(1.0, factor)

    return compute


def screen_saturation(color_key: str, factor: float) -> ComputeColorFn:
    """
    Scale the saturation of a color using the screen blend mode.

    Formula: new_saturation = 1 - (1 - saturation) * factor

    This is gentler than multiply and preserves more of the original color.

    :param color_key: The key of the color to scale.
    :type color_key: str
    :param factor: The scaling factor (0.0 to 2.0+). Values < 1.0 increase saturation,
                   values > 1.0 decrease it.
    :type factor: float
    :return: A function that computes the screened color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        new_saturation = max(0.0, min(1.0, 1.0 - (1.0 - color.saturation) * factor))
        return HSLColor(color.hue, new_saturation, color.lightness, color.opacity)

    return compute


def screen_lightness(color_key: str, factor: float) -> ComputeColorFn:
    """
    Scale the lightness of a color using the screen blend mode.

    Formula: new_lightness = 1 - (1 - lightness) * factor

    This is gentler than multiply and preserves more of the original color.

    :param color_key: The key of the color to scale.
    :type color_key: str
    :param factor: The scaling factor (0.0 to 2.0+). Values < 1.0 lighten,
                   values > 1.0 darken.
    :type factor: float
    :return: A function that computes the screened color.
    :rtype: ComputeColorFn
    """

    def compute(theme: Theme) -> HSLColor:
        color = theme.get_color(color_key)
        new_lightness = max(0.0, min(1.0, 1.0 - (1.0 - color.lightness) * factor))
        return HSLColor(color.hue, color.saturation, new_lightness, color.opacity)

    return compute


__all__ = [
    "adjust",
    "alias",
    "alpha",
    "brighten",
    "complementary",
    "contrast",
    "darker",
    "desaturate",
    "dim",
    "fade",
    "grayscale",
    "invert",
    "lighter",
    "mix",
    "multi",
    "muted",
    "rotate_hue",
    "saturate",
    "scale_lightness",
    "scale_saturation",
    "screen_lightness",
    "screen_saturation",
    "shade",
    "softer",
    "stronger",
    "tint",
    "tone",
]
