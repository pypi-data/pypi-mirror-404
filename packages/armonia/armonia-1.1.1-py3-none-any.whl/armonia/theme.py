"""Theme management for armonia."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

from polychromos.color import HSLColor
from polychromos.color.web import get_web_color
from polychromos.palette import HSLColorSequence

from armonia.exceptions import (
    ColorNameConflictError,
    ColorNotFoundError,
    ColorRecursionError,
    InvalidURIError,
    LogotypeNotFoundError,
)

# Type alias for computed color functions
ComputeColorFn = Callable[["Theme"], HSLColor]


def _is_valid_uri(uri: str) -> bool:
    """
    Validate if a string is a valid URI.

    Accepts various URI schemes including http, https, file, data, ftp, etc.
    A valid URI must have a scheme and should follow standard URI format.

    :param uri: The URI string to validate.
    :type uri: str
    :return: True if the URI is valid, False otherwise.
    :rtype: bool
    """
    if not uri:
        return False

    try:
        result = urlparse(uri)
        return bool(result.scheme and (result.netloc or result.path))
    except Exception:
        return False


@dataclass(frozen=True, slots=True)
class ThemeColorEntry:
    """Represents a theme color with metadata.

    :param name: The name of the color.
    :type name: str
    :param color: The resolved HSLColor value.
    :type color: HSLColor
    :param source: Whether this is a manual or computed color.
    :type source: Literal["manual", "computed"]
    """

    name: str
    color: HSLColor
    source: Literal["manual", "computed"]


class Theme:
    """A theme with custom color definitions."""

    def __init__(self) -> None:
        """Initialize a Theme with an empty dictionary of custom colors."""
        self.colors: dict[str, HSLColor] = {}
        self.computed_colors: dict[str, ComputeColorFn] = {}
        self.palettes: dict[str, list[str]] = {}
        self.logotypes: dict[str, str] = {}
        self._computing: set[str] = set()

    def _is_web_color(self, name: str) -> bool:
        """
        Check if a name is a reserved web color name.

        :param name: The color name to check.
        :type name: str
        :return: True if the name is a web color, False otherwise.
        :rtype: bool
        """
        try:
            get_web_color(name)
            return True
        except KeyError:
            return False

    def set_color(self, name: str, color: HSLColor) -> None:
        """
        Add or update a color in the theme.

        :param name: The name of the color to add or update.
        :type name: str
        :param color: The HSLColor value to associate with the name.
        :type color: HSLColor
        :raise ColorNameConflictError: When the name conflicts with a computed color
            or web color name.
        """
        if self._is_web_color(name):
            raise ColorNameConflictError(
                f"Cannot set color '{name}': name is a reserved web color."
            )

        if name in self.computed_colors:
            raise ColorNameConflictError(
                f"Cannot set color '{name}': name already exists as a computed color."
            )

        self.colors[name] = color

    def set_computed_color(self, name: str, compute_fn: ComputeColorFn) -> None:
        """
        Add or update a computed color in the theme.

        Computed colors are dynamically calculated based on the theme state.
        The compute function receives the theme instance and returns an HSLColor.

        :param name: The name of the computed color to add or update.
        :type name: str
        :param compute_fn: A callable that receives the theme and returns an HSLColor.
        :type compute_fn: Callable[[Theme], HSLColor]
        :raise ColorNameConflictError: When the name conflicts with a manual color
            or web color name.
        """
        if self._is_web_color(name):
            raise ColorNameConflictError(
                f"Cannot set computed color '{name}': name is a reserved web color."
            )

        if name in self.colors:
            raise ColorNameConflictError(
                f"Cannot set computed color '{name}': name already exists as a manual color."
            )

        self.computed_colors[name] = compute_fn

    def get_color(self, key: str) -> HSLColor:
        """
        Get a color by name or hex value with fallback resolution.

        Resolution order:
        1. Theme colors (custom colors defined in this theme)
        2. Computed colors (dynamically computed colors)
        3. Web colors (standard CSS/HTML color names)
        4. Hex colors (parse as hex color string like '#ff0000')

        :param key: The color name or hex value to look up.
        :type key: str
        :raise ColorNotFoundError: When the color cannot be found or parsed.
        :raise ColorRecursionError: When a computed color causes infinite recursion.
        :return: The resolved HSLColor.
        :rtype: HSLColor
        """
        if key in self.colors:
            return self.colors[key]

        if key in self.computed_colors:
            if key in self._computing:
                raise ColorRecursionError(
                    f"Circular dependency detected: '{key}' is already being computed. "
                    f"Check for cycles in computed color dependencies."
                )

            self._computing.add(key)
            try:
                return self.computed_colors[key](self)
            finally:
                self._computing.discard(key)

        try:
            return get_web_color(key)
        except KeyError:
            pass

        try:
            return HSLColor.from_hex(key)
        except (ValueError, Exception):
            pass

        raise ColorNotFoundError(
            f"Color '{key}' not found in theme colors, computed colors, "
            f"web colors, or as a valid hex color."
        )

    def remove_color(self, name: str) -> None:
        """
        Remove a manual color from the theme.

        :param name: The name of the color to remove.
        :type name: str
        :raise KeyError: When the color does not exist in the theme.
        """
        del self.colors[name]

    def remove_computed_color(self, name: str) -> None:
        """
        Remove a computed color from the theme.

        :param name: The name of the computed color to remove.
        :type name: str
        :raise KeyError: When the computed color does not exist in the theme.
        """
        del self.computed_colors[name]

    def set_palette(self, name: str, colors: list[str]) -> None:
        """
        Add or update a palette in the theme.

        A palette is a named collection of color references (color names or hex values).

        :param name: The name of the palette to add or update.
        :type name: str
        :param colors: A list of color names and/or hex values.
        :type colors: list[str]
        """
        self.palettes[name] = colors

    def get_palette(self, name: str) -> HSLColorSequence:
        """
        Get a palette by name, resolving all colors.

        :param name: The name of the palette to retrieve.
        :type name: str
        :return: An HSLColorSequence containing the resolved colors.
        :rtype: HSLColorSequence
        :raise KeyError: When the palette does not exist in the theme.
        """
        if name not in self.palettes:
            raise KeyError(f"Palette '{name}' not found in theme palettes.")

        return [self.get_color(color_ref) for color_ref in self.palettes[name]]

    def remove_palette(self, name: str) -> None:
        """
        Remove a palette from the theme.

        :param name: The name of the palette to remove.
        :type name: str
        :raise KeyError: When the palette does not exist in the theme.
        """
        del self.palettes[name]

    def set_logotype(self, name: str, uri: str) -> None:
        """
        Add or update a logotype in the theme.

        A logotype is a named URI reference to a logo resource.
        The URI is validated to ensure it follows standard URI format.

        :param name: The name of the logotype to add or update.
        :type name: str
        :param uri: The URI string pointing to the logo resource.
        :type uri: str
        :raise InvalidURIError: When the URI is not valid.

        Example::

            theme.set_logotype("company_logo", "https://example.com/logo.svg")
            theme.set_logotype("local_logo", "file://./logos/logo.png")
            theme.set_logotype("data_logo", "data:image/svg+xml,<svg>...</svg>")
        """
        if not _is_valid_uri(uri):
            raise InvalidURIError(
                f"Invalid URI provided for logotype '{name}': '{uri}'. "
                f"URI must be a valid URI string with a scheme (e.g., https://, file://, data:)."
            )

        self.logotypes[name] = uri

    def get_logotype(self, name: str) -> str:
        """
        Get a logotype URI by name.

        :param name: The name of the logotype to retrieve.
        :type name: str
        :return: The URI string for the logotype.
        :rtype: str
        :raise LogotypeNotFoundError: When the logotype does not exist in the theme.

        Example::

            theme.set_logotype("logo", "https://example.com/logo.svg")
            uri = theme.get_logotype("logo")
            # uri = "https://example.com/logo.svg"
        """
        if name not in self.logotypes:
            raise LogotypeNotFoundError(f"Logotype '{name}' not found in theme logotypes.")

        return self.logotypes[name]

    def remove_logotype(self, name: str) -> None:
        """
        Remove a logotype from the theme.

        :param name: The name of the logotype to remove.
        :type name: str
        :raise KeyError: When the logotype does not exist in the theme.
        """
        del self.logotypes[name]

    def get_all_colors(
        self,
        sort_by: Literal["name", "hue", "saturation", "lightness"] = "name",
        reverse: bool = False,
    ) -> list[ThemeColorEntry]:
        """
        Get all registered theme colors in an ordered list.

        This method returns both manual and computed colors with their final
        resolved values. Each entry includes the color name, the HSLColor value,
        and the source (manual or computed).

        :param sort_by: How to sort the colors. Options:
            - "name": Sort alphabetically by color name (default)
            - "hue": Sort by hue value (0-360 degrees)
            - "saturation": Sort by saturation value (0-1)
            - "lightness": Sort by lightness value (0-1)
        :type sort_by: Literal["name", "hue", "saturation", "lightness"]
        :param reverse: Whether to reverse the sort order.
        :type reverse: bool
        :return: A list of ThemeColorEntry objects with name, color, and source.
        :rtype: list[ThemeColorEntry]

        Example::

            theme = Theme()
            theme.set_color("primary", HSLColor.from_hex("#2563eb"))
            theme.set_color("accent", HSLColor.from_hex("#ff0000"))

            # Get all colors sorted by name
            colors = theme.get_all_colors(sort_by="name")
            for entry in colors:
                print(f"{entry.name}: {entry.color.to_css_hex()} ({entry.source})")

            # Get all colors sorted by hue
            colors_by_hue = theme.get_all_colors(sort_by="hue")

            # Get all colors sorted by lightness (darkest to lightest)
            colors_by_lightness = theme.get_all_colors(sort_by="lightness")
        """
        entries: list[ThemeColorEntry] = []

        for name, color in self.colors.items():
            entries.append(
                ThemeColorEntry(
                    name=name,
                    color=color,
                    source="manual",
                )
            )

        for name in self.computed_colors:
            try:
                color = self.get_color(name)
                entries.append(
                    ThemeColorEntry(
                        name=name,
                        color=color,
                        source="computed",
                    )
                )
            except (ColorNotFoundError, ColorRecursionError):
                pass

        if sort_by == "name":
            entries.sort(key=lambda e: e.name, reverse=reverse)
        elif sort_by == "hue":
            entries.sort(key=lambda e: e.color.hue, reverse=reverse)
        elif sort_by == "saturation":
            entries.sort(key=lambda e: e.color.saturation, reverse=reverse)
        elif sort_by == "lightness":
            entries.sort(key=lambda e: e.color.lightness, reverse=reverse)

        return entries

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Theme":
        """
        Create a Theme from a dictionary representation.

        This method deserializes a dictionary (e.g., loaded from JSON or YAML)
        into a Theme instance with colors, computed colors, and palettes.

        :param data: The dictionary representation of the theme.
        :type data: dict
        :return: A new Theme instance.
        :rtype: Theme

        Example::

            data = {
                "colors": {
                    "primary": "#2563eb",
                    "secondary": "#7c3aed"
                },
                "computed_colors": {
                    "primary_light": {
                        "function": "lighter",
                        "args": ["primary", 0.15]
                    }
                },
                "palettes": {
                    "primary_scale": ["primary_dark", "primary", "primary_light"]
                }
            }

            theme = Theme.from_dict(data)
        """
        from armonia.serialization import theme_from_dict

        return theme_from_dict(data)


__all__ = [
    "ComputeColorFn",
    "Theme",
    "ThemeColorEntry",
]
