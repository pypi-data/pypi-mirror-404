"""Unit tests for the Theme class."""

import pytest
from polychromos.color import HSLColor

from armonia.exceptions import (
    ColorNameConflictError,
    ColorNotFoundError,
    InvalidURIError,
    LogotypeNotFoundError,
)
from armonia.theme import Theme


class TestThemeInitialization:
    """Tests for Theme initialization."""

    def test_init_empty_colors(self) -> None:
        """Test that a new Theme has empty color dictionaries."""
        theme = Theme()
        assert theme.colors == {}
        assert theme.computed_colors == {}
        assert theme.palettes == {}
        assert theme.logotypes == {}


class TestSetColor:
    """Tests for the set_color method."""

    def test_set_single_color(self) -> None:
        """Test setting a single color."""
        theme = Theme()
        color = HSLColor.from_hex("#ff0000")
        theme.set_color("primary", color)
        assert "primary" in theme.colors
        assert theme.colors["primary"] == color

    def test_set_multiple_colors(self) -> None:
        """Test setting multiple colors."""
        theme = Theme()
        red = HSLColor.from_hex("#ff0000")
        blue = HSLColor.from_hex("#0000ff")
        theme.set_color("primary", red)
        theme.set_color("secondary", blue)
        assert len(theme.colors) == 2
        assert theme.colors["primary"] == red
        assert theme.colors["secondary"] == blue

    def test_set_color_overwrites_existing(self) -> None:
        """Test that setting a color with an existing name overwrites it."""
        theme = Theme()
        red = HSLColor.from_hex("#ff0000")
        blue = HSLColor.from_hex("#0000ff")
        theme.set_color("primary", red)
        theme.set_color("primary", blue)
        assert theme.colors["primary"] == blue


class TestSetComputedColor:
    """Tests for the set_computed_color method."""

    def test_set_computed_color(self) -> None:
        """Test setting a computed color."""
        theme = Theme()

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        theme.set_computed_color("computed", compute_fn)
        assert "computed" in theme.computed_colors
        assert theme.computed_colors["computed"] == compute_fn

    def test_set_multiple_computed_colors(self) -> None:
        """Test setting multiple computed colors."""
        theme = Theme()

        def compute_fn1(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        def compute_fn2(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#ff00ff")

        theme.set_computed_color("computed1", compute_fn1)
        theme.set_computed_color("computed2", compute_fn2)
        assert len(theme.computed_colors) == 2

    def test_computed_color_receives_theme(self) -> None:
        """Test that computed color function receives the theme instance."""
        theme = Theme()
        theme.set_color("base", HSLColor.from_hex("#ff0000"))

        def compute_fn(t: Theme) -> HSLColor:
            # Verify we can access theme colors from the compute function
            base_color = t.get_color("base")
            return HSLColor(
                base_color.hue,
                base_color.saturation,
                min(1.0, base_color.lightness + 0.2),
                base_color.opacity,
            )

        theme.set_computed_color("lighter", compute_fn)
        lighter = theme.get_color("lighter")
        base = theme.get_color("base")
        assert lighter.lightness > base.lightness


class TestGetColor:
    """Tests for the get_color method."""

    @pytest.mark.parametrize(
        ("color_name", "hex_value"),
        [
            ("primary", "#ff0000"),
            ("secondary", "#0000ff"),
            ("accent", "#00ff00"),
        ],
    )
    def test_get_theme_color(self, color_name: str, hex_value: str) -> None:
        """Test getting theme colors."""
        theme = Theme()
        color = HSLColor.from_hex(hex_value)
        theme.set_color(color_name, color)
        retrieved = theme.get_color(color_name)
        assert retrieved == color

    def test_get_computed_color(self) -> None:
        """Test getting computed colors."""
        theme = Theme()

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#123456")

        theme.set_computed_color("computed", compute_fn)
        color = theme.get_color("computed")
        assert color == HSLColor.from_hex("#123456")

    @pytest.mark.parametrize(
        ("color_name", "expected_hex"),
        [
            ("red", "#ff0000"),
            ("blue", "#0000ff"),
            ("green", "#008000"),
            ("white", "#ffffff"),
            ("black", "#000000"),
            ("orange", "#ffa500"),
            ("purple", "#800080"),
        ],
    )
    def test_get_web_color(self, color_name: str, expected_hex: str) -> None:
        """Test getting web colors."""
        theme = Theme()
        color = theme.get_color(color_name)
        assert color.to_css_hex() == expected_hex

    @pytest.mark.parametrize(
        "hex_value",
        [
            "#ff0000",
            "#00ff00",
            "#0000ff",
            "#123456",
            "#abcdef",
            "#FEDCBA",
        ],
    )
    def test_get_hex_color(self, hex_value: str) -> None:
        """Test getting colors by hex value."""
        theme = Theme()
        color = theme.get_color(hex_value)
        assert color.to_css_hex().lower() == hex_value.lower()

    def test_color_resolution_order_theme_first(self) -> None:
        """Test that theme colors have priority over computed colors."""
        theme = Theme()
        # Set both theme and computed color with same name
        theme_color = HSLColor.from_hex("#ff0000")
        theme.set_color("testcolor", theme_color)

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        # This should raise an error now
        with pytest.raises(ColorNameConflictError):
            theme.set_computed_color("testcolor", compute_fn)

    def test_color_resolution_order_computed_after_theme(self) -> None:
        """Test that computed colors come after theme colors in resolution."""
        theme = Theme()
        # Set a theme color
        theme_color = HSLColor.from_hex("#ff0000")
        theme.set_color("mycolor", theme_color)

        # Getting it should return the theme color
        color = theme.get_color("mycolor")
        assert color == theme_color

    def test_color_resolution_order_web_third(self) -> None:
        """Test that web colors come after theme and computed colors."""
        theme = Theme()
        # Access a web color directly
        color = theme.get_color("blue")
        # Should get the standard web color blue
        assert color.to_css_hex() == "#0000ff"

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "nonexistent",
            "not_a_color",
            "invalid",
            "#gggggg",  # Invalid hex
            "xyz",
        ],
    )
    def test_get_color_not_found(self, invalid_key: str) -> None:
        """Test that ColorNotFoundError is raised for invalid colors."""
        theme = Theme()
        with pytest.raises(ColorNotFoundError) as exc_info:
            theme.get_color(invalid_key)
        assert invalid_key in str(exc_info.value)


class TestRemoveColor:
    """Tests for the remove_color method."""

    def test_remove_existing_color(self) -> None:
        """Test removing an existing color."""
        theme = Theme()
        color = HSLColor.from_hex("#ff0000")
        theme.set_color("primary", color)
        theme.remove_color("primary")
        assert "primary" not in theme.colors

    def test_remove_nonexistent_color_raises_error(self) -> None:
        """Test that removing a nonexistent color raises KeyError."""
        theme = Theme()
        with pytest.raises(KeyError):
            theme.remove_color("nonexistent")

    def test_remove_color_does_not_affect_computed_colors(self) -> None:
        """Test that removing a color doesn't affect computed colors."""
        theme = Theme()
        theme.set_color("regular", HSLColor.from_hex("#ff0000"))

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        theme.set_computed_color("computed", compute_fn)
        theme.remove_color("regular")
        assert "computed" in theme.computed_colors


class TestRemoveComputedColor:
    """Tests for the remove_computed_color method."""

    def test_remove_existing_computed_color(self) -> None:
        """Test removing an existing computed color."""
        theme = Theme()

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#ff0000")

        theme.set_computed_color("computed", compute_fn)
        theme.remove_computed_color("computed")
        assert "computed" not in theme.computed_colors

    def test_remove_nonexistent_computed_color_raises_error(self) -> None:
        """Test that removing a nonexistent computed color raises KeyError."""
        theme = Theme()
        with pytest.raises(KeyError):
            theme.remove_computed_color("nonexistent")

    def test_remove_computed_color_does_not_affect_regular_colors(self) -> None:
        """Test that removing a computed color doesn't affect regular colors."""
        theme = Theme()
        theme.set_color("regular", HSLColor.from_hex("#ff0000"))

        def compute_fn(t: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        theme.set_computed_color("computed", compute_fn)
        theme.remove_computed_color("computed")
        assert "regular" in theme.colors


class TestComputedColorDynamicBehavior:
    """Tests for computed color dynamic behavior."""

    def test_computed_color_updates_with_theme_changes(self) -> None:
        """Test that computed colors reflect changes to their dependencies."""
        theme = Theme()
        theme.set_color("base", HSLColor.from_hex("#ff0000"))

        def lighter_base(t: Theme) -> HSLColor:
            base = t.get_color("base")
            return HSLColor(
                base.hue,
                base.saturation,
                min(1.0, base.lightness + 0.2),
                base.opacity,
            )

        theme.set_computed_color("lighter", lighter_base)

        # Get lighter color with red base
        lighter_red = theme.get_color("lighter")
        assert lighter_red.hue == HSLColor.from_hex("#ff0000").hue

        # Change base to blue
        theme.set_color("base", HSLColor.from_hex("#0000ff"))
        lighter_blue = theme.get_color("lighter")
        assert lighter_blue.hue == HSLColor.from_hex("#0000ff").hue
        assert lighter_red.hue != lighter_blue.hue

    def test_computed_color_chain(self) -> None:
        """Test that computed colors can depend on other computed colors."""
        theme = Theme()
        theme.set_color("base", HSLColor.from_hex("#ff0000"))

        def lighter(t: Theme) -> HSLColor:
            base = t.get_color("base")
            return HSLColor(
                base.hue,
                base.saturation,
                min(1.0, base.lightness + 0.1),
                base.opacity,
            )

        def even_lighter(t: Theme) -> HSLColor:
            lighter_color = t.get_color("lighter")
            return HSLColor(
                lighter_color.hue,
                lighter_color.saturation,
                min(1.0, lighter_color.lightness + 0.1),
                lighter_color.opacity,
            )

        theme.set_computed_color("lighter", lighter)
        theme.set_computed_color("even_lighter", even_lighter)

        base = theme.get_color("base")
        lighter_color = theme.get_color("lighter")
        even_lighter_color = theme.get_color("even_lighter")

        assert base.lightness < lighter_color.lightness < even_lighter_color.lightness


class TestColorNameConflicts:
    """Tests for color name conflict detection."""

    @pytest.mark.parametrize(
        "web_color_name",
        ["red", "blue", "green", "purple", "orange", "black", "white"],
    )
    def test_cannot_set_manual_color_with_web_color_name(
        self, web_color_name: str
    ) -> None:
        """Test that manual colors cannot use web color names."""
        theme = Theme()
        color = HSLColor.from_hex("#123456")
        with pytest.raises(ColorNameConflictError) as exc_info:
            theme.set_color(web_color_name, color)
        assert web_color_name in str(exc_info.value)
        assert "web color" in str(exc_info.value)

    @pytest.mark.parametrize(
        "web_color_name",
        ["red", "blue", "green", "purple", "orange", "black", "white"],
    )
    def test_cannot_set_computed_color_with_web_color_name(
        self, web_color_name: str
    ) -> None:
        """Test that computed colors cannot use web color names."""
        theme = Theme()

        def compute_fn(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#123456")

        with pytest.raises(ColorNameConflictError) as exc_info:
            theme.set_computed_color(web_color_name, compute_fn)
        assert web_color_name in str(exc_info.value)
        assert "web color" in str(exc_info.value)

    def test_cannot_set_computed_color_with_manual_color_name(self) -> None:
        """Test that computed colors cannot use existing manual color names."""
        theme = Theme()
        theme.set_color("mycolor", HSLColor.from_hex("#ff0000"))

        def compute_fn(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        with pytest.raises(ColorNameConflictError) as exc_info:
            theme.set_computed_color("mycolor", compute_fn)
        assert "mycolor" in str(exc_info.value)
        assert "manual color" in str(exc_info.value)

    def test_cannot_set_manual_color_with_computed_color_name(self) -> None:
        """Test that manual colors cannot use existing computed color names."""
        theme = Theme()

        def compute_fn(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#ff0000")

        theme.set_computed_color("mycomputed", compute_fn)

        with pytest.raises(ColorNameConflictError) as exc_info:
            theme.set_color("mycomputed", HSLColor.from_hex("#00ff00"))
        assert "mycomputed" in str(exc_info.value)
        assert "computed color" in str(exc_info.value)

    def test_can_overwrite_manual_color_with_same_type(self) -> None:
        """Test that manual colors can be overwritten with manual colors."""
        theme = Theme()
        theme.set_color("mycolor", HSLColor.from_hex("#ff0000"))
        # This should not raise an error
        theme.set_color("mycolor", HSLColor.from_hex("#00ff00"))
        assert theme.colors["mycolor"] == HSLColor.from_hex("#00ff00")

    def test_can_overwrite_computed_color_with_same_type(self) -> None:
        """Test that computed colors can be overwritten with computed colors."""
        theme = Theme()

        def compute_fn1(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#ff0000")

        def compute_fn2(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        theme.set_computed_color("mycomputed", compute_fn1)
        # This should not raise an error
        theme.set_computed_color("mycomputed", compute_fn2)
        assert theme.computed_colors["mycomputed"] == compute_fn2


class TestColorNotFoundError:
    """Tests for the ColorNotFoundError exception."""

    def test_error_message_includes_key(self) -> None:
        """Test that the error message includes the color key."""
        theme = Theme()
        with pytest.raises(ColorNotFoundError) as exc_info:
            theme.get_color("nonexistent_color")
        assert "nonexistent_color" in str(exc_info.value)

    def test_error_mentions_all_resolution_methods(self) -> None:
        """Test that error message mentions all resolution methods."""
        theme = Theme()
        with pytest.raises(ColorNotFoundError) as exc_info:
            theme.get_color("invalid")
        error_msg = str(exc_info.value)
        assert "theme colors" in error_msg
        assert "computed colors" in error_msg
        assert "web colors" in error_msg
        assert "hex color" in error_msg


class TestPalettes:
    """Tests for palette functionality."""

    def test_set_palette_with_hex_colors(self) -> None:
        """Test setting a palette with hex color values."""
        theme = Theme()
        palette_colors = ["#ff0000", "#00ff00", "#0000ff"]
        theme.set_palette("primary", palette_colors)
        assert "primary" in theme.palettes
        assert theme.palettes["primary"] == palette_colors

    def test_set_palette_with_color_names(self) -> None:
        """Test setting a palette with color names."""
        theme = Theme()
        palette_colors = ["red", "green", "blue"]
        theme.set_palette("web_colors", palette_colors)
        assert "web_colors" in theme.palettes
        assert theme.palettes["web_colors"] == palette_colors

    def test_set_palette_with_mixed_values(self) -> None:
        """Test setting a palette with mixed color names and hex values."""
        theme = Theme()
        palette_colors = ["red", "#00ff00", "blue", "#ffff00"]
        theme.set_palette("mixed", palette_colors)
        assert theme.palettes["mixed"] == palette_colors

    def test_set_palette_with_theme_colors(self) -> None:
        """Test setting a palette with theme color references."""
        theme = Theme()
        theme.set_color("primary", HSLColor.from_hex("#ff0000"))
        theme.set_color("secondary", HSLColor.from_hex("#00ff00"))
        palette_colors = ["primary", "secondary", "blue"]
        theme.set_palette("my_palette", palette_colors)
        assert theme.palettes["my_palette"] == palette_colors

    def test_set_palette_overwrites_existing(self) -> None:
        """Test that setting a palette with existing name overwrites it."""
        theme = Theme()
        theme.set_palette("test", ["red", "green"])
        theme.set_palette("test", ["blue", "yellow"])
        assert theme.palettes["test"] == ["blue", "yellow"]

    def test_set_empty_palette(self) -> None:
        """Test setting an empty palette."""
        theme = Theme()
        theme.set_palette("empty", [])
        assert "empty" in theme.palettes
        assert theme.palettes["empty"] == []

    def test_get_palette_with_hex_colors(self) -> None:
        """Test getting a palette with hex colors returns HSLColorSequence."""
        theme = Theme()
        palette_colors = ["#ff0000", "#00ff00", "#0000ff"]
        theme.set_palette("primary", palette_colors)

        result = theme.get_palette("primary")
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == HSLColor.from_hex("#ff0000")
        assert result[1] == HSLColor.from_hex("#00ff00")
        assert result[2] == HSLColor.from_hex("#0000ff")

    def test_get_palette_with_web_colors(self) -> None:
        """Test getting a palette with web color names."""
        theme = Theme()
        theme.set_palette("web", ["red", "green", "blue"])

        result = theme.get_palette("web")
        assert isinstance(result, list)
        assert len(result) == 3
        # Web colors should be resolved correctly
        assert result[0].to_css_hex() == "#ff0000"
        assert result[1].to_css_hex() == "#008000"  # Web green is #008000
        assert result[2].to_css_hex() == "#0000ff"

    def test_get_palette_with_theme_colors(self) -> None:
        """Test getting a palette that references theme colors."""
        theme = Theme()
        theme.set_color("custom_red", HSLColor.from_hex("#cc0000"))
        theme.set_color("custom_blue", HSLColor.from_hex("#0000cc"))
        theme.set_palette("custom", ["custom_red", "custom_blue"])

        result = theme.get_palette("custom")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == HSLColor.from_hex("#cc0000")
        assert result[1] == HSLColor.from_hex("#0000cc")

    def test_get_palette_with_computed_colors(self) -> None:
        """Test getting a palette that references computed colors."""
        theme = Theme()
        theme.set_color("base", HSLColor.from_hex("#ff0000"))

        def lighter_base(t: Theme) -> HSLColor:
            base = t.get_color("base")
            return HSLColor(
                base.hue,
                base.saturation,
                min(1.0, base.lightness + 0.2),
                base.opacity,
            )

        theme.set_computed_color("lighter", lighter_base)
        theme.set_palette("computed_palette", ["base", "lighter"])

        result = theme.get_palette("computed_palette")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[1].lightness > result[0].lightness

    def test_get_palette_with_mixed_sources(self) -> None:
        """Test getting a palette with colors from different sources."""
        theme = Theme()
        theme.set_color("custom", HSLColor.from_hex("#abcdef"))
        theme.set_palette("mixed", ["custom", "red", "#123456"])

        result = theme.get_palette("mixed")
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == HSLColor.from_hex("#abcdef")
        assert result[1].to_css_hex() == "#ff0000"  # web red
        assert result[2] == HSLColor.from_hex("#123456")

    def test_get_palette_nonexistent_raises_error(self) -> None:
        """Test that getting a nonexistent palette raises KeyError."""
        theme = Theme()
        with pytest.raises(KeyError) as exc_info:
            theme.get_palette("nonexistent")
        assert "nonexistent" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    def test_get_empty_palette(self) -> None:
        """Test getting an empty palette returns empty HSLColorSequence."""
        theme = Theme()
        theme.set_palette("empty", [])
        result = theme.get_palette("empty")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_remove_palette(self) -> None:
        """Test removing an existing palette."""
        theme = Theme()
        theme.set_palette("test", ["red", "blue"])
        theme.remove_palette("test")
        assert "test" not in theme.palettes

    def test_remove_nonexistent_palette_raises_error(self) -> None:
        """Test that removing a nonexistent palette raises KeyError."""
        theme = Theme()
        with pytest.raises(KeyError):
            theme.remove_palette("nonexistent")

    def test_palette_updates_with_theme_changes(self) -> None:
        """Test that palette colors reflect changes to theme colors."""
        theme = Theme()
        theme.set_color("dynamic", HSLColor.from_hex("#ff0000"))
        theme.set_palette("test", ["dynamic"])

        # Get palette with red
        result1 = theme.get_palette("test")
        assert result1[0] == HSLColor.from_hex("#ff0000")

        # Change the theme color
        theme.set_color("dynamic", HSLColor.from_hex("#0000ff"))

        # Get palette again - should reflect the change
        result2 = theme.get_palette("test")
        assert result2[0] == HSLColor.from_hex("#0000ff")

    def test_multiple_palettes(self) -> None:
        """Test managing multiple palettes simultaneously."""
        theme = Theme()
        theme.set_palette("palette1", ["red", "green"])
        theme.set_palette("palette2", ["blue", "yellow"])
        theme.set_palette("palette3", ["#ffffff", "#000000"])

        assert len(theme.palettes) == 3
        assert "palette1" in theme.palettes
        assert "palette2" in theme.palettes
        assert "palette3" in theme.palettes

        # Verify each palette can be retrieved independently
        p1 = theme.get_palette("palette1")
        p2 = theme.get_palette("palette2")
        p3 = theme.get_palette("palette3")

        assert len(p1) == 2
        assert len(p2) == 2
        assert len(p3) == 2

    def test_palette_with_invalid_color_raises_error(self) -> None:
        """Test that getting a palette with invalid color reference raises error."""
        theme = Theme()
        theme.set_palette("bad_palette", ["nonexistent_color"])

        with pytest.raises(ColorNotFoundError):
            theme.get_palette("bad_palette")


class TestGetAllColors:
    """Tests for the get_all_colors method."""

    def test_get_all_colors_empty_theme(self) -> None:
        """Test getting all colors from an empty theme."""
        theme = Theme()
        colors = theme.get_all_colors()
        assert isinstance(colors, list)
        assert len(colors) == 0

    def test_get_all_colors_manual_only(self) -> None:
        """Test getting all colors when only manual colors exist."""
        theme = Theme()
        theme.set_color("primary", HSLColor.from_hex("#ff0000"))
        theme.set_color("secondary", HSLColor.from_hex("#00ff00"))
        theme.set_color("accent", HSLColor.from_hex("#0000ff"))

        colors = theme.get_all_colors()
        assert len(colors) == 3

        # Check that all colors are present
        names = {c.name for c in colors}
        assert names == {"primary", "secondary", "accent"}

        # Check that all are manual
        for entry in colors:
            assert entry.source == "manual"

    def test_get_all_colors_computed_only(self) -> None:
        """Test getting all colors when only computed colors exist."""
        theme = Theme()

        def red_fn(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#ff0000")

        def green_fn(_: Theme) -> HSLColor:
            return HSLColor.from_hex("#00ff00")

        theme.set_computed_color("computed_red", red_fn)
        theme.set_computed_color("computed_green", green_fn)

        colors = theme.get_all_colors()
        assert len(colors) == 2

        # Check that all are computed
        for entry in colors:
            assert entry.source == "computed"

    def test_get_all_colors_mixed_sources(self) -> None:
        """Test getting all colors with both manual and computed colors."""
        theme = Theme()
        theme.set_color("primary", HSLColor.from_hex("#ff0000"))

        def lighter_primary(t: Theme) -> HSLColor:
            base = t.get_color("primary")
            return HSLColor(
                base.hue,
                base.saturation,
                min(1.0, base.lightness + 0.2),
                base.opacity,
            )

        theme.set_computed_color("primary_light", lighter_primary)

        colors = theme.get_all_colors()
        assert len(colors) == 2

        # Find each color
        manual_colors = [c for c in colors if c.source == "manual"]
        computed_colors = [c for c in colors if c.source == "computed"]

        assert len(manual_colors) == 1
        assert len(computed_colors) == 1
        assert manual_colors[0].name == "primary"
        assert computed_colors[0].name == "primary_light"

    def test_get_all_colors_sort_by_name(self) -> None:
        """Test sorting colors by name."""
        theme = Theme()
        theme.set_color("zebra", HSLColor.from_hex("#ff0000"))
        theme.set_color("apple", HSLColor.from_hex("#00ff00"))
        theme.set_color("banana", HSLColor.from_hex("#0000ff"))

        colors = theme.get_all_colors(sort_by="name")
        names = [c.name for c in colors]
        assert names == ["apple", "banana", "zebra"]

    def test_get_all_colors_sort_by_name_reverse(self) -> None:
        """Test sorting colors by name in reverse order."""
        theme = Theme()
        theme.set_color("zebra", HSLColor.from_hex("#ff0000"))
        theme.set_color("apple", HSLColor.from_hex("#00ff00"))
        theme.set_color("banana", HSLColor.from_hex("#0000ff"))

        colors = theme.get_all_colors(sort_by="name", reverse=True)
        names = [c.name for c in colors]
        assert names == ["zebra", "banana", "apple"]

    def test_get_all_colors_sort_by_hue(self) -> None:
        """Test sorting colors by hue."""
        theme = Theme()
        # Red: hue ~0, Green: hue ~120, Blue: hue ~240
        theme.set_color("color_red", HSLColor.from_hex("#ff0000"))
        theme.set_color("color_green", HSLColor.from_hex("#00ff00"))
        theme.set_color("color_blue", HSLColor.from_hex("#0000ff"))

        colors = theme.get_all_colors(sort_by="hue")
        names = [c.name for c in colors]
        # Should be sorted by hue: red (0), green (~120), blue (~240)
        assert names == ["color_red", "color_green", "color_blue"]

    def test_get_all_colors_sort_by_saturation(self) -> None:
        """Test sorting colors by saturation."""
        theme = Theme()
        # Create colors with different saturations
        theme.set_color("vivid", HSLColor(0, 1.0, 0.5, 1.0))  # Full saturation
        theme.set_color("muted", HSLColor(0, 0.3, 0.5, 1.0))  # Low saturation
        theme.set_color("desaturated", HSLColor(0, 0.0, 0.5, 1.0))  # No saturation

        colors = theme.get_all_colors(sort_by="saturation")
        names = [c.name for c in colors]
        assert names == ["desaturated", "muted", "vivid"]

    def test_get_all_colors_sort_by_lightness(self) -> None:
        """Test sorting colors by lightness."""
        theme = Theme()
        theme.set_color("dark", HSLColor(0, 1.0, 0.2, 1.0))
        theme.set_color("medium", HSLColor(0, 1.0, 0.5, 1.0))
        theme.set_color("light", HSLColor(0, 1.0, 0.8, 1.0))

        colors = theme.get_all_colors(sort_by="lightness")
        names = [c.name for c in colors]
        assert names == ["dark", "medium", "light"]

    def test_get_all_colors_includes_computed_values(self) -> None:
        """Test that computed colors are resolved to their actual values."""
        theme = Theme()
        theme.set_color("base", HSLColor.from_hex("#ff0000"))

        def lighter(t: Theme) -> HSLColor:
            base = t.get_color("base")
            return HSLColor(
                base.hue,
                base.saturation,
                min(1.0, base.lightness + 0.2),
                base.opacity,
            )

        theme.set_computed_color("lighter", lighter)

        colors = theme.get_all_colors()
        lighter_entry = next(c for c in colors if c.name == "lighter")

        # Verify the color is computed
        assert lighter_entry.source == "computed"
        # Verify it has the actual computed value, not a placeholder
        assert lighter_entry.color.lightness > theme.colors["base"].lightness

    def test_get_all_colors_skips_broken_computed_colors(self) -> None:
        """Test that computed colors with errors are skipped."""
        theme = Theme()

        def broken_fn(t: Theme) -> HSLColor:
            # This will fail because "nonexistent" doesn't exist
            return t.get_color("nonexistent")

        theme.set_computed_color("broken", broken_fn)
        theme.set_color("working", HSLColor.from_hex("#ff0000"))

        colors = theme.get_all_colors()

        # Should only have the working color
        assert len(colors) == 1
        assert colors[0].name == "working"

    def test_get_all_colors_return_type(self) -> None:
        """Test that get_all_colors returns the correct type."""
        from armonia.theme import ThemeColorEntry

        theme = Theme()
        theme.set_color("test", HSLColor.from_hex("#ff0000"))

        colors = theme.get_all_colors()
        assert isinstance(colors, list)
        assert all(isinstance(c, ThemeColorEntry) for c in colors)

    def test_get_all_colors_entry_attributes(self) -> None:
        """Test that ThemeColorEntry has the expected attributes."""
        theme = Theme()
        theme.set_color("test", HSLColor.from_hex("#ff0000"))

        colors = theme.get_all_colors()
        entry = colors[0]

        # Check all required attributes exist
        assert hasattr(entry, "name")
        assert hasattr(entry, "color")
        assert hasattr(entry, "source")

        # Check types
        assert isinstance(entry.name, str)
        assert isinstance(entry.color, HSLColor)
        assert entry.source in ("manual", "computed")


class TestLogotypes:
    """Tests for logotype functionality."""

    def test_set_logotype_with_https_url(self) -> None:
        """Test setting a logotype with an HTTPS URL."""
        theme = Theme()
        uri = "https://example.com/logo.svg"
        theme.set_logotype("company_logo", uri)
        assert "company_logo" in theme.logotypes
        assert theme.logotypes["company_logo"] == uri

    def test_set_logotype_with_http_url(self) -> None:
        """Test setting a logotype with an HTTP URL."""
        theme = Theme()
        uri = "http://example.com/logo.png"
        theme.set_logotype("logo", uri)
        assert theme.logotypes["logo"] == uri

    def test_set_logotype_with_file_uri(self) -> None:
        """Test setting a logotype with a file:// URI."""
        theme = Theme()
        uri = "file:///path/to/logo.svg"
        theme.set_logotype("local_logo", uri)
        assert theme.logotypes["local_logo"] == uri

    def test_set_logotype_with_data_uri(self) -> None:
        """Test setting a logotype with a data: URI."""
        theme = Theme()
        uri = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        theme.set_logotype("inline_logo", uri)
        assert theme.logotypes["inline_logo"] == uri

    def test_set_multiple_logotypes(self) -> None:
        """Test setting multiple logotypes."""
        theme = Theme()
        uri1 = "https://example.com/logo1.svg"
        uri2 = "https://example.com/logo2.png"
        theme.set_logotype("logo1", uri1)
        theme.set_logotype("logo2", uri2)
        assert len(theme.logotypes) == 2
        assert theme.logotypes["logo1"] == uri1
        assert theme.logotypes["logo2"] == uri2

    def test_set_logotype_overwrites_existing(self) -> None:
        """Test that setting a logotype with existing name overwrites it."""
        theme = Theme()
        uri1 = "https://example.com/old-logo.svg"
        uri2 = "https://example.com/new-logo.svg"
        theme.set_logotype("logo", uri1)
        theme.set_logotype("logo", uri2)
        assert theme.logotypes["logo"] == uri2

    @pytest.mark.parametrize(
        "invalid_uri",
        [
            "not-a-uri",
            "just some text",
            "",
            "example.com",  # Missing scheme
            "://no-scheme",
        ],
    )
    def test_set_logotype_with_invalid_uri_raises_error(
        self, invalid_uri: str
    ) -> None:
        """Test that setting an invalid URI raises InvalidURIError."""
        theme = Theme()
        with pytest.raises(InvalidURIError) as exc_info:
            theme.set_logotype("logo", invalid_uri)
        assert "Invalid URI" in str(exc_info.value)
        assert invalid_uri in str(exc_info.value)

    def test_set_logotype_with_ftp_uri(self) -> None:
        """Test that FTP URIs are accepted as valid."""
        theme = Theme()
        uri = "ftp://example.com/logo.svg"
        theme.set_logotype("ftp_logo", uri)
        assert theme.logotypes["ftp_logo"] == uri

    def test_get_logotype(self) -> None:
        """Test getting a logotype by name."""
        theme = Theme()
        uri = "https://example.com/logo.svg"
        theme.set_logotype("logo", uri)
        retrieved = theme.get_logotype("logo")
        assert retrieved == uri

    def test_get_logotype_not_found_raises_error(self) -> None:
        """Test that getting a nonexistent logotype raises LogotypeNotFoundError."""
        theme = Theme()
        with pytest.raises(LogotypeNotFoundError) as exc_info:
            theme.get_logotype("nonexistent")
        assert "nonexistent" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    def test_remove_logotype(self) -> None:
        """Test removing an existing logotype."""
        theme = Theme()
        uri = "https://example.com/logo.svg"
        theme.set_logotype("logo", uri)
        theme.remove_logotype("logo")
        assert "logo" not in theme.logotypes

    def test_remove_nonexistent_logotype_raises_error(self) -> None:
        """Test that removing a nonexistent logotype raises KeyError."""
        theme = Theme()
        with pytest.raises(KeyError):
            theme.remove_logotype("nonexistent")

    def test_logotypes_independent_from_colors(self) -> None:
        """Test that logotypes and colors are independent."""
        theme = Theme()
        theme.set_color("primary", HSLColor.from_hex("#ff0000"))
        theme.set_logotype("logo", "https://example.com/logo.svg")

        # Both should coexist
        assert "primary" in theme.colors
        assert "logo" in theme.logotypes

        # Removing one shouldn't affect the other
        theme.remove_color("primary")
        assert "logo" in theme.logotypes

        theme.remove_logotype("logo")
        assert "primary" not in theme.colors

    def test_logotype_with_query_parameters(self) -> None:
        """Test setting a logotype with query parameters in the URL."""
        theme = Theme()
        uri = "https://example.com/logo.svg?version=2&format=svg"
        theme.set_logotype("logo", uri)
        assert theme.get_logotype("logo") == uri

    def test_logotype_with_fragment(self) -> None:
        """Test setting a logotype with a fragment identifier."""
        theme = Theme()
        uri = "https://example.com/logos.svg#logo-primary"
        theme.set_logotype("logo", uri)
        assert theme.get_logotype("logo") == uri

    def test_multiple_logotypes_different_schemes(self) -> None:
        """Test that multiple logotypes with different URI schemes work."""
        theme = Theme()
        theme.set_logotype("web_logo", "https://example.com/logo.svg")
        theme.set_logotype("local_logo", "file:///logos/logo.png")
        theme.set_logotype("data_logo", "data:image/svg+xml,<svg></svg>")

        assert len(theme.logotypes) == 3
        assert theme.get_logotype("web_logo").startswith("https://")
        assert theme.get_logotype("local_logo").startswith("file://")
        assert theme.get_logotype("data_logo").startswith("data:")
