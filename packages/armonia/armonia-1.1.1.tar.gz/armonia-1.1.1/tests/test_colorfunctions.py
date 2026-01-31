"""Unit tests for color transformation functions."""

import pytest
from polychromos.color import HSLColor

from armonia import colorfunctions as cf
from armonia.theme import Theme


class TestLighterDarker:
    """Tests for lighter and darker functions."""

    def test_lighter_increases_lightness(self) -> None:
        """Test that lighter increases the lightness of a color."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("light", cf.lighter("base", 0.2))

        base = theme.get_color("base")
        light = theme.get_color("light")

        assert light.lightness > base.lightness
        assert abs(light.lightness - base.lightness - 0.2) < 0.01

    def test_darker_decreases_lightness(self) -> None:
        """Test that darker decreases the lightness of a color."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("dark", cf.darker("base", 0.2))

        base = theme.get_color("base")
        dark = theme.get_color("dark")

        assert dark.lightness < base.lightness
        assert abs(base.lightness - dark.lightness - 0.2) < 0.01

    def test_lighter_with_default_amount(self) -> None:
        """Test lighter with default amount."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("light", cf.lighter("base"))

        base = theme.get_color("base")
        light = theme.get_color("light")

        assert abs(light.lightness - base.lightness - 0.1) < 0.01


class TestSaturateDesaturate:
    """Tests for saturate and desaturate functions."""

    def test_saturate_increases_saturation(self) -> None:
        """Test that saturate increases the saturation of a color."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.5, 0.5, 1.0))
        theme.set_computed_color("vivid", cf.saturate("base", 0.2))

        base = theme.get_color("base")
        vivid = theme.get_color("vivid")

        assert vivid.saturation > base.saturation
        assert abs(vivid.saturation - base.saturation - 0.2) < 0.01

    def test_desaturate_decreases_saturation(self) -> None:
        """Test that desaturate decreases the saturation of a color."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("dull", cf.desaturate("base", 0.3))

        base = theme.get_color("base")
        dull = theme.get_color("dull")

        assert dull.saturation < base.saturation
        assert abs(base.saturation - dull.saturation - 0.3) < 0.01

    def test_muted_is_desaturated(self) -> None:
        """Test that muted is equivalent to desaturate."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("muted", cf.muted("base"))

        base = theme.get_color("base")
        muted = theme.get_color("muted")

        # Default mute amount is 0.3
        assert abs(base.saturation - muted.saturation - 0.3) < 0.01


class TestBrightenDim:
    """Tests for brighten and dim functions."""

    def test_brighten_is_lighter(self) -> None:
        """Test that brighten increases lightness."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.4, 1.0))
        theme.set_computed_color("bright", cf.brighten("base"))

        base = theme.get_color("base")
        bright = theme.get_color("bright")

        # Default brighten amount is 0.2
        assert abs(bright.lightness - base.lightness - 0.2) < 0.01

    def test_dim_is_darker(self) -> None:
        """Test that dim decreases lightness."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("dimmed", cf.dim("base"))

        base = theme.get_color("base")
        dimmed = theme.get_color("dimmed")

        # Default dim amount is 0.2
        assert abs(base.lightness - dimmed.lightness - 0.2) < 0.01


class TestRotateHue:
    """Tests for rotate_hue function."""

    def test_rotate_hue_positive(self) -> None:
        """Test rotating hue in positive direction."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.0, 0.8, 0.5, 1.0))  # Red
        theme.set_computed_color("rotated", cf.rotate_hue("base", 120))  # To Green

        rotated = theme.get_color("rotated")
        # 120 degrees is 1/3 of the circle
        assert abs(rotated.hue - 0.333333) < 0.01

    def test_rotate_hue_negative(self) -> None:
        """Test rotating hue in negative direction."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("rotated", cf.rotate_hue("base", -60))

        base = theme.get_color("base")
        rotated = theme.get_color("rotated")

        # -60 degrees wraps around
        expected_hue = (base.hue - 60 / 360.0) % 1.0
        assert abs(rotated.hue - expected_hue) < 0.01

    def test_rotate_hue_preserves_other_components(self) -> None:
        """Test that rotating hue doesn't affect saturation or lightness."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("rotated", cf.rotate_hue("base", 180))

        base = theme.get_color("base")
        rotated = theme.get_color("rotated")

        assert rotated.saturation == base.saturation
        assert rotated.lightness == base.lightness
        assert rotated.opacity == base.opacity


class TestAdjust:
    """Tests for the adjust function."""

    def test_adjust_multiple_components(self) -> None:
        """Test adjusting multiple color components."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.5, 0.5, 1.0))
        theme.set_computed_color(
            "adjusted",
            cf.adjust("base", hue_delta=0.1, saturation_delta=0.2, lightness_delta=-0.1),
        )

        base = theme.get_color("base")
        adjusted = theme.get_color("adjusted")

        assert abs(adjusted.hue - (base.hue + 0.1)) < 0.01
        assert abs(adjusted.saturation - (base.saturation + 0.2)) < 0.01
        assert abs(adjusted.lightness - (base.lightness - 0.1)) < 0.01

    def test_adjust_opacity(self) -> None:
        """Test adjusting opacity."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.5, 0.5, 1.0))
        theme.set_computed_color("transparent", cf.adjust("base", opacity_delta=-0.5))

        adjusted = theme.get_color("transparent")
        assert abs(adjusted.opacity - 0.5) < 0.01


class TestAlphaFade:
    """Tests for alpha and fade functions."""

    def test_alpha_sets_opacity(self) -> None:
        """Test that alpha sets the opacity to a specific value."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("semi_transparent", cf.alpha("base", 0.5))

        result = theme.get_color("semi_transparent")
        assert abs(result.opacity - 0.5) < 0.01

    def test_fade_is_alias_for_alpha(self) -> None:
        """Test that fade is an alias for alpha."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("faded", cf.fade("base", 0.3))

        result = theme.get_color("faded")
        assert abs(result.opacity - 0.3) < 0.01

    def test_alpha_preserves_other_components(self) -> None:
        """Test that alpha doesn't affect other color components."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("transparent", cf.alpha("base", 0.5))

        base = theme.get_color("base")
        transparent = theme.get_color("transparent")

        assert transparent.hue == base.hue
        assert transparent.saturation == base.saturation
        assert transparent.lightness == base.lightness


class TestMix:
    """Tests for mix function."""

    def test_mix_two_colors_50_50(self) -> None:
        """Test mixing two colors with equal weight."""
        theme = Theme()
        theme.set_color("color1", HSLColor(0.0, 1.0, 0.3, 1.0))
        theme.set_color("color2", HSLColor(0.0, 1.0, 0.7, 1.0))
        theme.set_computed_color("mixed_color", cf.mix("color1", "color2", 0.5))

        color1 = theme.get_color("color1")
        color2 = theme.get_color("color2")
        mixed_color = theme.get_color("mixed_color")

        # Mixed color should have intermediate lightness
        assert color1.lightness < mixed_color.lightness < color2.lightness

    def test_mix_with_weight_0(self) -> None:
        """Test mixing with weight 0 returns first color."""
        theme = Theme()
        theme.set_color("color1", HSLColor(0.0, 1.0, 0.5, 1.0))
        theme.set_color("color2", HSLColor(0.5, 1.0, 0.5, 1.0))
        theme.set_computed_color("mixed", cf.mix("color1", "color2", 0.0))

        color1 = theme.get_color("color1")
        mixed = theme.get_color("mixed")

        assert abs(mixed.hue - color1.hue) < 0.01
        assert abs(mixed.saturation - color1.saturation) < 0.01
        assert abs(mixed.lightness - color1.lightness) < 0.01

    def test_mix_with_weight_1(self) -> None:
        """Test mixing with weight 1 returns second color."""
        theme = Theme()
        theme.set_color("color1", HSLColor(0.0, 1.0, 0.5, 1.0))
        theme.set_color("color2", HSLColor(0.5, 1.0, 0.5, 1.0))
        theme.set_computed_color("mixed", cf.mix("color1", "color2", 1.0))

        color2 = theme.get_color("color2")
        mixed = theme.get_color("mixed")

        assert abs(mixed.hue - color2.hue) < 0.01
        assert abs(mixed.saturation - color2.saturation) < 0.01
        assert abs(mixed.lightness - color2.lightness) < 0.01


class TestSofterStronger:
    """Tests for softer and stronger functions."""

    def test_softer_shifts_towards_background(self) -> None:
        """Test that softer shifts color towards background."""
        theme = Theme()
        theme.set_color("foreground", HSLColor(0.0, 1.0, 0.5, 1.0))  # Bright red
        theme.set_color("background", HSLColor(0.0, 0.0, 0.9, 1.0))  # Light gray
        theme.set_computed_color("soft", cf.softer("foreground", "background", 0.3))

        foreground = theme.get_color("foreground")
        soft = theme.get_color("soft")

        # Softer color should have less saturation (shifted towards gray background)
        assert soft.saturation < foreground.saturation

    def test_stronger_increases_saturation(self) -> None:
        """Test that stronger increases saturation."""
        theme = Theme()
        theme.set_color("foreground", HSLColor(0.0, 0.5, 0.5, 1.0))
        theme.set_color("background", HSLColor(0.0, 0.0, 0.9, 1.0))
        theme.set_computed_color("strong", cf.stronger("foreground", "background", 0.3))

        foreground = theme.get_color("foreground")
        strong = theme.get_color("strong")

        # Stronger color should have more saturation
        assert strong.saturation > foreground.saturation


class TestComplementary:
    """Tests for complementary function."""

    def test_complementary_opposite_hue(self) -> None:
        """Test that complementary returns opposite hue."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.0, 1.0, 0.5, 1.0))  # Red
        theme.set_computed_color("comp", cf.complementary("base"))

        comp = theme.get_color("comp")
        # Complementary of red (0.0) should be cyan (0.5)
        assert abs(comp.hue - 0.5) < 0.01

    def test_complementary_with_muting(self) -> None:
        """Test complementary with saturation and lightness muting."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.0, 1.0, 0.5, 1.0))
        theme.set_computed_color(
            "comp", cf.complementary("base", mute_saturation=0.2, mute_lightness=0.1)
        )

        base = theme.get_color("base")
        comp = theme.get_color("comp")

        assert comp.saturation < base.saturation
        assert comp.lightness < base.lightness


class TestGrayscale:
    """Tests for grayscale function."""

    def test_grayscale_removes_saturation(self) -> None:
        """Test that grayscale removes all saturation."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("grayscale_version", cf.grayscale("base"))

        grayscale_version = theme.get_color("grayscale_version")
        assert grayscale_version.saturation == 0.0

    def test_grayscale_preserves_lightness(self) -> None:
        """Test that grayscale preserves lightness."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("grayscale_version", cf.grayscale("base"))

        base = theme.get_color("base")
        grayscale_version = theme.get_color("grayscale_version")

        assert grayscale_version.lightness == base.lightness


class TestInvert:
    """Tests for invert function."""

    def test_invert_inverts_lightness(self) -> None:
        """Test that invert inverts the lightness."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.7, 1.0))
        theme.set_computed_color("inverted", cf.invert("base"))

        inverted = theme.get_color("inverted")
        assert abs(inverted.lightness - 0.3) < 0.01

    def test_invert_preserves_hue_and_saturation(self) -> None:
        """Test that invert preserves hue and saturation."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.7, 1.0))
        theme.set_computed_color("inverted", cf.invert("base"))

        base = theme.get_color("base")
        inverted = theme.get_color("inverted")

        assert inverted.hue == base.hue
        assert inverted.saturation == base.saturation


class TestTintShadeTone:
    """Tests for tint, shade, and tone functions."""

    def test_tint_lightens_color(self) -> None:
        """Test that tint lightens a color by mixing with white."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.4, 1.0))
        theme.set_computed_color("tinted", cf.tint("base", 0.2))

        base = theme.get_color("base")
        tinted = theme.get_color("tinted")

        assert tinted.lightness > base.lightness

    def test_shade_darkens_color(self) -> None:
        """Test that shade darkens a color by mixing with black."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("shaded", cf.shade("base", 0.2))

        base = theme.get_color("base")
        shaded = theme.get_color("shaded")

        assert shaded.lightness < base.lightness

    def test_tone_reduces_saturation(self) -> None:
        """Test that tone reduces saturation by mixing with gray."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("toned", cf.tone("base", 0.3))

        base = theme.get_color("base")
        toned = theme.get_color("toned")

        assert toned.saturation < base.saturation


class TestContrast:
    """Tests for contrast function."""

    def test_contrast_returns_dark_for_light_background(self) -> None:
        """Test that contrast returns dark color for light background."""
        theme = Theme()
        theme.set_color("light_bg", HSLColor(0.5, 0.5, 0.8, 1.0))  # Light background
        theme.set_computed_color("text", cf.contrast("light_bg"))

        text = theme.get_color("text")
        # Web color "black"
        black = theme.get_color("black")

        # Should return black for light background
        assert text.lightness == black.lightness

    def test_contrast_returns_light_for_dark_background(self) -> None:
        """Test that contrast returns light color for dark background."""
        theme = Theme()
        theme.set_color("dark_bg", HSLColor(0.5, 0.5, 0.2, 1.0))  # Dark background
        theme.set_computed_color("text", cf.contrast("dark_bg"))

        text = theme.get_color("text")
        # Web color "white"
        white = theme.get_color("white")

        # Should return white for dark background
        assert text.lightness == white.lightness

    def test_contrast_with_custom_colors(self) -> None:
        """Test contrast with custom light and dark colors."""
        theme = Theme()
        theme.set_color("bg", HSLColor(0.5, 0.5, 0.8, 1.0))
        theme.set_color("custom_light", HSLColor(0.1, 0.5, 0.9, 1.0))
        theme.set_color("custom_dark", HSLColor(0.7, 0.5, 0.1, 1.0))
        theme.set_computed_color(
            "text", cf.contrast("bg", "custom_light", "custom_dark")
        )

        text = theme.get_color("text")
        custom_dark = theme.get_color("custom_dark")

        # Should use custom dark for light background
        assert abs(text.hue - custom_dark.hue) < 0.01


class TestChaining:
    """Tests for chaining multiple transformations."""

    def test_chain_lighter_and_desaturate(self) -> None:
        """Test chaining lighter and desaturate transformations."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.4, 1.0))
        theme.set_computed_color("light", cf.lighter("base", 0.2))
        theme.set_computed_color("light_muted", cf.desaturate("light", 0.3))

        base = theme.get_color("base")
        light_muted = theme.get_color("light_muted")

        assert light_muted.lightness > base.lightness
        assert light_muted.saturation < base.saturation

    def test_dynamic_updates_with_computed_colors(self) -> None:
        """Test that computed colors update when base changes."""
        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("primary_light", cf.lighter("primary", 0.2))

        # Get initial light color
        initial_light = theme.get_color("primary_light")

        # Change primary color
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.3, 1.0))

        # Get updated light color
        updated_light = theme.get_color("primary_light")

        # The light colors should be different
        assert initial_light.lightness != updated_light.lightness


class TestAlias:
    """Tests for alias function."""

    def test_alias_returns_same_color(self) -> None:
        """Test that alias returns the exact same color."""
        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("brand", cf.alias("primary"))

        primary = theme.get_color("primary")
        brand = theme.get_color("brand")

        assert brand.hue == primary.hue
        assert brand.saturation == primary.saturation
        assert brand.lightness == primary.lightness
        assert brand.opacity == primary.opacity

    def test_alias_updates_with_source(self) -> None:
        """Test that aliased color updates when source changes."""
        theme = Theme()
        theme.set_color("primary", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("brand", cf.alias("primary"))

        # Change primary
        theme.set_color("primary", HSLColor(0.3, 0.7, 0.5, 0.9))

        brand = theme.get_color("brand")
        primary = theme.get_color("primary")

        assert brand.hue == primary.hue
        assert brand.saturation == primary.saturation
        assert brand.lightness == primary.lightness
        assert brand.opacity == primary.opacity


class TestMulti:
    """Tests for multi function."""

    def test_multi_applies_transformations_sequentially(self) -> None:
        """Test that multi applies multiple transformations in order."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))

        # Apply lighter then desaturate
        theme.set_computed_color(
            "transformed",
            cf.multi(
                "base",
                lambda c: c.delta(0, 0, 0.2),  # lighter by 0.2
                lambda c: c.delta(0, -0.3, 0),  # desaturate by 0.3
            ),
        )

        base = theme.get_color("base")
        transformed = theme.get_color("transformed")

        # Should be lighter and less saturated
        assert abs(transformed.lightness - (base.lightness + 0.2)) < 0.01
        assert abs(transformed.saturation - (base.saturation - 0.3)) < 0.01
        assert transformed.hue == base.hue

    def test_multi_with_single_transform(self) -> None:
        """Test multi with just one transformation."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color(
            "transformed", cf.multi("base", lambda c: c.delta(0, 0, 0.1))
        )

        base = theme.get_color("base")
        transformed = theme.get_color("transformed")

        assert abs(transformed.lightness - (base.lightness + 0.1)) < 0.01

    def test_multi_with_complex_transformations(self) -> None:
        """Test multi with more complex transformations."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.6, 0.5, 1.0))

        theme.set_computed_color(
            "complex",
            cf.multi(
                "base",
                lambda c: c.delta(0.1, 0, 0),  # rotate hue
                lambda c: c.delta(0, 0.2, 0),  # saturate
                lambda c: c.delta(0, 0, -0.1),  # darken
                lambda c: c.delta(0, 0, 0, -0.2),  # reduce opacity
            ),
        )

        base = theme.get_color("base")
        complex_color = theme.get_color("complex")

        # Verify all transformations were applied
        assert complex_color.hue != base.hue
        assert complex_color.saturation > base.saturation
        assert complex_color.lightness < base.lightness
        assert complex_color.opacity < base.opacity


class TestScaleSaturation:
    """Tests for scale_saturation function."""

    def test_scale_saturation_decrease(self) -> None:
        """Test scaling saturation down with factor < 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("scaled", cf.scale_saturation("base", 0.5))

        base = theme.get_color("base")
        scaled = theme.get_color("scaled")

        # Should be half the saturation
        assert abs(scaled.saturation - (base.saturation * 0.5)) < 0.01
        # Other components unchanged
        assert scaled.hue == base.hue
        assert scaled.lightness == base.lightness

    def test_scale_saturation_increase(self) -> None:
        """Test scaling saturation up with factor > 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.5, 0.5, 1.0))
        theme.set_computed_color("scaled", cf.scale_saturation("base", 1.5))

        base = theme.get_color("base")
        scaled = theme.get_color("scaled")

        # Should be 1.5x the saturation
        expected = min(1.0, base.saturation * 1.5)
        assert abs(scaled.saturation - expected) < 0.01

    def test_scale_saturation_clamps_at_one(self) -> None:
        """Test that scaled saturation is clamped at 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("scaled", cf.scale_saturation("base", 2.0))

        scaled = theme.get_color("scaled")
        assert scaled.saturation <= 1.0


class TestScaleLightness:
    """Tests for scale_lightness function."""

    def test_scale_lightness_decrease(self) -> None:
        """Test scaling lightness down with factor < 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.6, 1.0))
        theme.set_computed_color("scaled", cf.scale_lightness("base", 0.5))

        base = theme.get_color("base")
        scaled = theme.get_color("scaled")

        # Should be half the lightness
        assert abs(scaled.lightness - (base.lightness * 0.5)) < 0.01
        # Other components unchanged
        assert scaled.hue == base.hue
        assert scaled.saturation == base.saturation

    def test_scale_lightness_increase(self) -> None:
        """Test scaling lightness up with factor > 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.4, 1.0))
        theme.set_computed_color("scaled", cf.scale_lightness("base", 1.5))

        base = theme.get_color("base")
        scaled = theme.get_color("scaled")

        # Should be 1.5x the lightness
        expected = min(1.0, base.lightness * 1.5)
        assert abs(scaled.lightness - expected) < 0.01

    def test_scale_lightness_clamps_at_one(self) -> None:
        """Test that scaled lightness is clamped at 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.8, 1.0))
        theme.set_computed_color("scaled", cf.scale_lightness("base", 2.0))

        scaled = theme.get_color("scaled")
        assert scaled.lightness <= 1.0


class TestScreenSaturation:
    """Tests for screen_saturation function."""

    def test_screen_saturation_increase(self) -> None:
        """Test screen mode increases saturation with factor < 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.5, 0.5, 1.0))
        theme.set_computed_color("screened", cf.screen_saturation("base", 0.5))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        # Screen formula: 1 - (1 - s) * factor
        expected = 1.0 - (1.0 - base.saturation) * 0.5
        assert abs(screened.saturation - expected) < 0.01
        assert screened.saturation > base.saturation

    def test_screen_saturation_decrease(self) -> None:
        """Test screen mode decreases saturation with factor > 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.5, 1.0))
        theme.set_computed_color("screened", cf.screen_saturation("base", 1.5))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        # Screen formula: 1 - (1 - s) * factor
        expected = max(0.0, 1.0 - (1.0 - base.saturation) * 1.5)
        assert abs(screened.saturation - expected) < 0.01

    def test_screen_saturation_preserves_other_components(self) -> None:
        """Test that screen_saturation doesn't affect other components."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.6, 0.7, 0.9))
        theme.set_computed_color("screened", cf.screen_saturation("base", 0.8))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        assert screened.hue == base.hue
        assert screened.lightness == base.lightness
        assert screened.opacity == base.opacity


class TestScreenLightness:
    """Tests for screen_lightness function."""

    def test_screen_lightness_increase(self) -> None:
        """Test screen mode increases lightness with factor < 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.4, 1.0))
        theme.set_computed_color("screened", cf.screen_lightness("base", 0.5))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        # Screen formula: 1 - (1 - l) * factor
        expected = 1.0 - (1.0 - base.lightness) * 0.5
        assert abs(screened.lightness - expected) < 0.01
        assert screened.lightness > base.lightness

    def test_screen_lightness_decrease(self) -> None:
        """Test screen mode decreases lightness with factor > 1.0."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.8, 0.7, 1.0))
        theme.set_computed_color("screened", cf.screen_lightness("base", 1.5))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        # Screen formula: 1 - (1 - l) * factor
        expected = max(0.0, 1.0 - (1.0 - base.lightness) * 1.5)
        assert abs(screened.lightness - expected) < 0.01

    def test_screen_lightness_preserves_other_components(self) -> None:
        """Test that screen_lightness doesn't affect other components."""
        theme = Theme()
        theme.set_color("base", HSLColor(0.5, 0.6, 0.7, 0.9))
        theme.set_computed_color("screened", cf.screen_lightness("base", 0.8))

        base = theme.get_color("base")
        screened = theme.get_color("screened")

        assert screened.hue == base.hue
        assert screened.saturation == base.saturation
        assert screened.opacity == base.opacity
