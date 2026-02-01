"""Extract CSS styles and convert colors to LUXBIN wavelengths."""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class CSSRule:
    selector: str
    properties: List[Tuple[str, str]]  # (property, value)


@dataclass
class ColorMapping:
    css_color: str  # original CSS color string
    r: int
    g: int
    b: int
    wavelength_nm: float


def parse_css(css_text: str) -> List[CSSRule]:
    """Parse CSS text into a list of rules (selector + properties)."""
    rules: List[CSSRule] = []
    # Strip comments
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

    for match in re.finditer(r'([^{}]+)\{([^}]*)\}', css_text):
        selector = match.group(1).strip()
        body = match.group(2).strip()
        props: List[Tuple[str, str]] = []
        for decl in body.split(';'):
            decl = decl.strip()
            if ':' in decl:
                prop, _, val = decl.partition(':')
                props.append((prop.strip(), val.strip()))
        if props:
            rules.append(CSSRule(selector=selector, properties=props))
    return rules


def extract_colors(rules: List[CSSRule]) -> List[ColorMapping]:
    """Extract all color values from CSS rules and map to wavelengths."""
    color_props = {"color", "background-color", "background", "border-color",
                   "outline-color", "fill", "stroke"}
    mappings: List[ColorMapping] = []
    seen = set()

    for rule in rules:
        for prop, val in rule.properties:
            if prop not in color_props:
                continue
            rgb = _parse_color(val)
            if rgb and val not in seen:
                seen.add(val)
                r, g, b = rgb
                wl = rgb_to_wavelength(r, g, b)
                mappings.append(ColorMapping(css_color=val, r=r, g=g, b=b, wavelength_nm=wl))
    return mappings


def _parse_color(val: str) -> Optional[Tuple[int, int, int]]:
    """Try to parse a CSS color value to (r, g, b)."""
    val = val.strip().lower()

    # hex
    m = re.match(r'^#([0-9a-f]{6})$', val)
    if m:
        h = m.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    m = re.match(r'^#([0-9a-f]{3})$', val)
    if m:
        h = m.group(1)
        return int(h[0]*2, 16), int(h[1]*2, 16), int(h[2]*2, 16)

    # rgb()
    m = re.match(r'^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$', val)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    # named colors (small subset)
    named = {
        "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
        "white": (255, 255, 255), "black": (0, 0, 0), "yellow": (255, 255, 0),
        "cyan": (0, 255, 255), "magenta": (255, 0, 255), "orange": (255, 165, 0),
        "purple": (128, 0, 128), "gray": (128, 128, 128), "grey": (128, 128, 128),
        "pink": (255, 192, 203),
    }
    if val in named:
        return named[val]

    return None


def rgb_to_wavelength(r: int, g: int, b: int) -> float:
    """Map an RGB color to an approximate dominant wavelength in the visible spectrum.

    Returns wavelength in nm (400-700 range).
    """
    # Determine dominant hue via simple max-channel approach
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == mn:
        return 550.0  # neutral grey → middle of spectrum

    if mx == r:
        hue = 60.0 * ((g - b) / (mx - mn)) % 360
    elif mx == g:
        hue = 60.0 * ((b - r) / (mx - mn)) + 120
    else:
        hue = 60.0 * ((r - g) / (mx - mn)) + 240
    hue = hue % 360

    # Map hue 0-360 to wavelength 400-700nm
    # Hue 0/360=red(~700nm), 120=green(~550nm), 240=blue(~450nm)
    if hue <= 120:
        # red→green: 700→550
        wavelength = 700.0 - (hue / 120.0) * 150.0
    elif hue <= 240:
        # green→blue: 550→450
        wavelength = 550.0 - ((hue - 120.0) / 120.0) * 100.0
    else:
        # blue→red: 450→400 then wrap
        wavelength = 450.0 - ((hue - 240.0) / 120.0) * 50.0

    return round(max(400.0, min(700.0, wavelength)), 1)
