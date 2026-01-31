"""Serialization support for color functions and themes.

This module provides utilities for serializing and deserializing color functions
and themes to/from dictionaries, enabling storage in JSON, YAML, or other formats.
"""

from typing import Any, cast

from polychromos.color import HSLColor

from armonia import colorfunctions as cf
from armonia.theme import ComputeColorFn, Theme

_FUNCTION_REGISTRY: dict[str, dict[str, Any]] = {
    "lighter": {
        "fn": cf.lighter,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "darker": {
        "fn": cf.darker,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "saturate": {
        "fn": cf.saturate,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "desaturate": {
        "fn": cf.desaturate,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "muted": {
        "fn": cf.muted,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.3},
    },
    "brighten": {
        "fn": cf.brighten,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.2},
    },
    "dim": {
        "fn": cf.dim,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.2},
    },
    "rotate_hue": {
        "fn": cf.rotate_hue,
        "params": ["color_key", "degrees"],
        "defaults": {},
    },
    "adjust": {
        "fn": cf.adjust,
        "params": [
            "color_key",
            "hue_delta",
            "saturation_delta",
            "lightness_delta",
            "opacity_delta",
        ],
        "defaults": {
            "hue_delta": 0.0,
            "saturation_delta": 0.0,
            "lightness_delta": 0.0,
            "opacity_delta": 0.0,
        },
    },
    "alpha": {
        "fn": cf.alpha,
        "params": ["color_key", "opacity"],
        "defaults": {},
    },
    "fade": {
        "fn": cf.fade,
        "params": ["color_key", "opacity"],
        "defaults": {},
    },
    "mix": {
        "fn": cf.mix,
        "params": ["color_key1", "color_key2", "weight"],
        "defaults": {"weight": 0.5},
    },
    "softer": {
        "fn": cf.softer,
        "params": ["color_key", "background_key", "amount"],
        "defaults": {"amount": 0.3},
    },
    "stronger": {
        "fn": cf.stronger,
        "params": ["color_key", "background_key", "amount"],
        "defaults": {"amount": 0.3},
    },
    "complementary": {
        "fn": cf.complementary,
        "params": ["color_key", "mute_saturation", "mute_lightness"],
        "defaults": {"mute_saturation": 0.0, "mute_lightness": 0.0},
    },
    "grayscale": {
        "fn": cf.grayscale,
        "params": ["color_key"],
        "defaults": {},
    },
    "invert": {
        "fn": cf.invert,
        "params": ["color_key"],
        "defaults": {},
    },
    "tint": {
        "fn": cf.tint,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "shade": {
        "fn": cf.shade,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "tone": {
        "fn": cf.tone,
        "params": ["color_key", "amount"],
        "defaults": {"amount": 0.1},
    },
    "contrast": {
        "fn": cf.contrast,
        "params": ["color_key", "light_color_key", "dark_color_key"],
        "defaults": {"light_color_key": "white", "dark_color_key": "black"},
    },
    "alias": {
        "fn": cf.alias,
        "params": ["color_key"],
        "defaults": {},
    },
    "scale_saturation": {
        "fn": cf.scale_saturation,
        "params": ["color_key", "factor"],
        "defaults": {},
    },
    "scale_lightness": {
        "fn": cf.scale_lightness,
        "params": ["color_key", "factor"],
        "defaults": {},
    },
    "screen_saturation": {
        "fn": cf.screen_saturation,
        "params": ["color_key", "factor"],
        "defaults": {},
    },
    "screen_lightness": {
        "fn": cf.screen_lightness,
        "params": ["color_key", "factor"],
        "defaults": {},
    },
}


def deserialize_computed_color(spec: dict[str, Any]) -> ComputeColorFn:
    """
    Deserialize a computed color function from a dictionary specification.

    Expected format::

        {
            "function": "lighter",
            "args": {
                "color_key": "primary",
                "amount": 0.2
            }
        }

    Or with positional arguments::

        {
            "function": "lighter",
            "args": ["primary", 0.2]
        }

    :param spec: The dictionary specification of the computed color.
    :type spec: dict[str, Any]
    :return: A compute function that can be used with set_computed_color.
    :rtype: ComputeColorFn
    :raises ValueError: If the specification is invalid or references an unknown function.
    """
    if "function" not in spec:
        raise ValueError("Computed color spec must have a 'function' field")

    function_name = spec["function"]
    if function_name not in _FUNCTION_REGISTRY:
        raise ValueError(
            f"Unknown color function: {function_name}. "
            f"Available functions: {', '.join(_FUNCTION_REGISTRY.keys())}"
        )

    registry_entry = _FUNCTION_REGISTRY[function_name]
    fn = registry_entry["fn"]
    params = registry_entry["params"]
    defaults = registry_entry["defaults"]

    args_spec = spec.get("args", {})

    if isinstance(args_spec, list):
        if len(args_spec) > len(params):
            raise ValueError(
                f"Too many arguments for {function_name}: "
                f"expected at most {len(params)}, got {len(args_spec)}"
            )
        kwargs = dict(zip(params, args_spec, strict=False))
    elif isinstance(args_spec, dict):
        kwargs = args_spec.copy()
    else:
        raise ValueError(f"'args' must be a list or dict, got {type(args_spec).__name__}")

    for param in params:
        if param not in kwargs and param in defaults:
            kwargs[param] = defaults[param]

    for param in params:
        if param not in kwargs and param not in defaults:
            raise ValueError(f"Missing required parameter '{param}' for {function_name}")

    return cast(ComputeColorFn, fn(**kwargs))


def theme_from_dict(data: dict[str, Any]) -> Theme:
    """
    Create a Theme from a dictionary representation.

    Expected format::

        {
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
            },
            "logotypes": {
                "company_logo": "https://example.com/logo.svg",
                "favicon": "https://example.com/favicon.ico"
            }
        }

    :param data: The dictionary representation of the theme.
    :type data: dict[str, Any]
    :return: A new Theme instance.
    :rtype: Theme
    """
    theme = Theme()

    colors = data.get("colors", {})
    for name, hex_value in colors.items():
        theme.set_color(name, HSLColor.from_hex(hex_value))

    computed_colors = data.get("computed_colors", {})
    for name, spec in computed_colors.items():
        compute_fn = deserialize_computed_color(spec)
        theme.set_computed_color(name, compute_fn)

    palettes = data.get("palettes", {})
    for name, color_refs in palettes.items():
        theme.set_palette(name, color_refs)

    logotypes = data.get("logotypes", {})
    for name, uri in logotypes.items():
        theme.set_logotype(name, uri)

    return theme


__all__ = [
    "deserialize_computed_color",
    "theme_from_dict",
]
