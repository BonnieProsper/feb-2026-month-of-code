# src/themes.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.colors import HexColor


Theme = Dict[str, Any]


THEMES: dict[str, Theme] = {
    "minimal": {
        "accent": HexColor("#2F80ED"),
        "text": HexColor("#111111"),
        "muted": HexColor("#555555"),
        "font": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "base_font_size": 10,
        "header_font_size": 16,
        "line_height": 12,
        "row_padding": 6,
        "rule_gap": 8,
        "currency_symbol": "$",
    },
    "modern": {
        "accent": HexColor("#111827"),
        "text": HexColor("#111111"),
        "muted": HexColor("#6B7280"),
        "font": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "base_font_size": 10,
        "header_font_size": 17,
        "line_height": 13,
        "row_padding": 7,
        "rule_gap": 9,
        "currency_symbol": "$",
    },
}


def load_theme(name: str, override_path: str | None = None) -> Theme:
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}")

    theme = dict(THEMES[name])

    if override_path:
        path = Path(override_path)
        if not path.exists():
            raise ValueError(f"Theme override not found: {override_path}")

        data = json.loads(path.read_text(encoding="utf-8"))

        for key, value in data.items():
            if key not in theme:
                raise ValueError(f"Invalid theme key: {key}")

            if key in {"accent", "text", "muted"}:
                theme[key] = HexColor(value)
            else:
                theme[key] = value

    return theme
