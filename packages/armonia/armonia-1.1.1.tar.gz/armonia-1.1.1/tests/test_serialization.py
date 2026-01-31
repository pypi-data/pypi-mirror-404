"""Unit tests for theme serialization and deserialization."""

import pytest
from polychromos.color import HSLColor

from armonia import serialization
from armonia.exceptions import InvalidURIError
from armonia.theme import Theme


class TestDeserializeComputedColor:
    """Tests for deserializing computed color specifications."""

    def test_deserialize_lighter_with_positional_args(self) -> None:
        """Test deserializing lighter function with positional arguments."""
        spec = {"function": "lighter", "args": ["primary", 0.2]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.5, 1.0))
        result = compute_fn(theme)

        assert result.lightness > 0.5
        assert abs(result.lightness - 0.7) < 0.01

    def test_deserialize_lighter_with_keyword_args(self) -> None:
        """Test deserializing lighter function with keyword arguments."""
        spec = {"function": "lighter", "args": {"color_key": "primary", "amount": 0.2}}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.5, 1.0))
        result = compute_fn(theme)

        assert result.lightness > 0.5
        assert abs(result.lightness - 0.7) < 0.01

    def test_deserialize_with_default_params(self) -> None:
        """Test deserializing function using default parameters."""
        spec = {"function": "lighter", "args": ["primary"]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.5, 1.0))
        result = compute_fn(theme)

        # Default amount is 0.1
        assert abs(result.lightness - 0.6) < 0.01

    def test_deserialize_mix_with_multiple_keys(self) -> None:
        """Test deserializing mix function with multiple color keys."""
        spec = {"function": "mix", "args": ["color1", "color2", 0.5]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("color1", HSLColor(0.0, 1.0, 0.3, 1.0))
        theme.set_color("color2", HSLColor(0.0, 1.0, 0.7, 1.0))
        result = compute_fn(theme)

        # Should be mixed 50/50
        assert 0.3 < result.lightness < 0.7

    def test_deserialize_alias(self) -> None:
        """Test deserializing alias function."""
        spec = {"function": "alias", "args": ["primary"]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.6, 1.0))
        result = compute_fn(theme)

        primary = theme.get_color("primary")
        assert result.hue == primary.hue
        assert result.saturation == primary.saturation
        assert result.lightness == primary.lightness

    def test_deserialize_scale_functions(self) -> None:
        """Test deserializing scale functions."""
        spec = {"function": "scale_lightness", "args": ["primary", 0.7]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.6, 1.0))
        result = compute_fn(theme)

        # Should be 0.6 * 0.7 = 0.42
        assert abs(result.lightness - 0.42) < 0.01

    def test_deserialize_screen_functions(self) -> None:
        """Test deserializing screen functions."""
        spec = {"function": "screen_lightness", "args": ["primary", 0.5]}
        compute_fn = serialization.deserialize_computed_color(spec)

        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.4, 1.0))
        result = compute_fn(theme)

        # Screen formula: 1 - (1 - 0.4) * 0.5 = 1 - 0.3 = 0.7
        assert abs(result.lightness - 0.7) < 0.01

    def test_deserialize_unknown_function_raises_error(self) -> None:
        """Test that deserializing unknown function raises ValueError."""
        spec = {"function": "nonexistent", "args": []}

        with pytest.raises(ValueError, match="Unknown color function"):
            serialization.deserialize_computed_color(spec)

    def test_deserialize_missing_function_field_raises_error(self) -> None:
        """Test that missing function field raises ValueError."""
        spec = {"args": ["primary", 0.2]}

        with pytest.raises(ValueError, match="must have a 'function' field"):
            serialization.deserialize_computed_color(spec)

    def test_deserialize_missing_required_param_raises_error(self) -> None:
        """Test that missing required parameter raises ValueError."""
        spec = {"function": "lighter", "args": {}}

        with pytest.raises(ValueError, match="Missing required parameter"):
            serialization.deserialize_computed_color(spec)

    def test_deserialize_too_many_positional_args_raises_error(self) -> None:
        """Test that too many positional arguments raises ValueError."""
        spec = {"function": "lighter", "args": ["primary", 0.2, "extra", "args"]}

        with pytest.raises(ValueError, match="Too many arguments"):
            serialization.deserialize_computed_color(spec)


class TestThemeFromDict:
    """Tests for creating Theme from dictionary."""

    def test_theme_from_dict_with_colors(self) -> None:
        """Test creating theme from dictionary with colors."""
        data = {"colors": {"primary": "#2563eb", "secondary": "#7c3aed"}}

        theme = Theme.from_dict(data)

        primary = theme.get_color("primary")
        assert primary.to_css_hex() == "#2563eb"

        secondary = theme.get_color("secondary")
        assert secondary.to_css_hex() == "#7c3aed"

    def test_theme_from_dict_with_computed_colors(self) -> None:
        """Test creating theme from dictionary with computed colors."""
        data = {
            "colors": {"primary": "#2563eb"},
            "computed_colors": {
                "primary_light": {"function": "lighter", "args": ["primary", 0.2]}
            },
        }

        theme = Theme.from_dict(data)

        primary = theme.get_color("primary")
        primary_light = theme.get_color("primary_light")

        assert primary_light.lightness > primary.lightness

    def test_theme_from_dict_with_palettes(self) -> None:
        """Test creating theme from dictionary with palettes."""
        data = {
            "colors": {"primary": "#2563eb"},
            "palettes": {"primary_scale": ["primary"]},
        }

        theme = Theme.from_dict(data)

        palette = theme.get_palette("primary_scale")
        assert len(palette) == 1
        assert palette[0].to_css_hex() == "#2563eb"

    def test_theme_from_dict_complex_example(self) -> None:
        """Test creating theme from dictionary with all features."""
        data = {
            "colors": {
                "primary": "#2563eb",
                "secondary": "#7c3aed",
                "background": "#ffffff",
            },
            "computed_colors": {
                "primary_light": {"function": "lighter", "args": ["primary", 0.15]},
                "primary_dark": {"function": "darker", "args": ["primary", 0.15]},
                "primary_muted": {"function": "muted", "args": ["primary", 0.4]},
                "brand": {"function": "alias", "args": ["primary"]},
                "primary_scaled": {
                    "function": "scale_lightness",
                    "args": ["primary", 0.7],
                },
            },
            "palettes": {
                "primary_scale": ["primary_dark", "primary", "primary_light"],
                "all_colors": ["primary", "secondary", "background"],
            },
        }

        theme = Theme.from_dict(data)

        # Check base colors
        assert theme.get_color("primary").to_css_hex() == "#2563eb"
        assert theme.get_color("secondary").to_css_hex() == "#7c3aed"

        # Check computed colors
        primary = theme.get_color("primary")
        primary_light = theme.get_color("primary_light")
        primary_dark = theme.get_color("primary_dark")
        brand = theme.get_color("brand")

        assert primary_light.lightness > primary.lightness
        assert primary_dark.lightness < primary.lightness
        assert brand == primary

        # Check palettes
        primary_scale = theme.get_palette("primary_scale")
        assert len(primary_scale) == 3

        all_colors = theme.get_palette("all_colors")
        assert len(all_colors) == 3

    def test_theme_from_dict_empty_data(self) -> None:
        """Test creating theme from empty dictionary."""
        data = {}
        theme = Theme.from_dict(data)

        # Should create valid empty theme
        assert len(theme.colors) == 0
        assert len(theme.computed_colors) == 0
        assert len(theme.palettes) == 0
        assert len(theme.logotypes) == 0

    def test_theme_from_dict_with_logotypes(self) -> None:
        """Test creating theme from dictionary with logotypes."""
        data = {
            "logotypes": {
                "company_logo": "https://example.com/logo.svg",
                "favicon": "https://example.com/favicon.ico",
            }
        }

        theme = Theme.from_dict(data)

        assert "company_logo" in theme.logotypes
        assert "favicon" in theme.logotypes
        assert theme.get_logotype("company_logo") == "https://example.com/logo.svg"
        assert theme.get_logotype("favicon") == "https://example.com/favicon.ico"

    def test_theme_from_dict_with_multiple_logotypes(self) -> None:
        """Test creating theme with multiple logotypes of different URI schemes."""
        data = {
            "logotypes": {
                "web_logo": "https://example.com/logo.svg",
                "local_logo": "file:///path/to/logo.png",
                "data_icon": "data:image/svg+xml,<svg></svg>",
                "ftp_asset": "ftp://example.com/logo.png",
            }
        }

        theme = Theme.from_dict(data)

        assert len(theme.logotypes) == 4
        assert theme.get_logotype("web_logo") == "https://example.com/logo.svg"
        assert theme.get_logotype("local_logo") == "file:///path/to/logo.png"
        assert theme.get_logotype("data_icon") == "data:image/svg+xml,<svg></svg>"
        assert theme.get_logotype("ftp_asset") == "ftp://example.com/logo.png"

    def test_theme_from_dict_with_invalid_logotype_uri(self) -> None:
        """Test that invalid logotype URI raises InvalidURIError."""
        data = {
            "logotypes": {
                "bad_logo": "not-a-valid-uri",
            }
        }

        with pytest.raises(InvalidURIError):
            Theme.from_dict(data)

    def test_theme_from_dict_complex_with_logotypes(self) -> None:
        """Test creating theme from dictionary with all features including logotypes."""
        data = {
            "colors": {
                "primary": "#2563eb",
                "secondary": "#7c3aed",
            },
            "computed_colors": {
                "primary_light": {"function": "lighter", "args": ["primary", 0.15]},
            },
            "palettes": {
                "primary_scale": ["primary", "primary_light"],
            },
            "logotypes": {
                "company_logo": "https://example.com/logo.svg",
                "dark_logo": "https://example.com/logo-dark.svg",
                "favicon": "https://example.com/favicon.ico",
            },
        }

        theme = Theme.from_dict(data)

        # Check colors
        assert theme.get_color("primary").to_css_hex() == "#2563eb"
        assert theme.get_color("primary_light").lightness > theme.get_color("primary").lightness

        # Check palettes
        palette = theme.get_palette("primary_scale")
        assert len(palette) == 2

        # Check logotypes
        assert len(theme.logotypes) == 3
        assert theme.get_logotype("company_logo") == "https://example.com/logo.svg"
        assert theme.get_logotype("dark_logo") == "https://example.com/logo-dark.svg"
        assert theme.get_logotype("favicon") == "https://example.com/favicon.ico"

    def test_theme_from_dict_empty_logotypes(self) -> None:
        """Test creating theme with empty logotypes section."""
        data = {
            "colors": {"primary": "#2563eb"},
            "logotypes": {},
        }

        theme = Theme.from_dict(data)

        assert len(theme.logotypes) == 0
        assert theme.get_color("primary").to_css_hex() == "#2563eb"
