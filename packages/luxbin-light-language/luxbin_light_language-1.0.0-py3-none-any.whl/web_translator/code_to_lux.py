"""Mode 2: Translate HTML/CSS/JS source into .lux program source code."""

import re
from typing import List, Tuple

from web_translator.html_parser import PageContent
from web_translator.css_extractor import CSSRule, ColorMapping, parse_css, extract_colors
from web_translator.js_extractor import JSContent, parse_js


# ---------------------------------------------------------------------------
# HTML → .lux
# ---------------------------------------------------------------------------

def html_to_lux(page: PageContent) -> str:
    """Translate parsed HTML content into a .lux program."""
    lines: List[str] = [
        "# =============================================",
        "# LUXBIN Light Language - Web Page Translation",
        "# =============================================",
        "",
    ]

    # Title
    if page.title:
        lines.append(f'photon_print("=== {_esc(page.title)} ===")')
        lines.append("")

    # Headings + paragraphs interleaved by order
    for level, text in page.headings:
        prefix = "=" * (5 - min(level, 4))
        lines.append(f'photon_print("{prefix} {_esc(text)} {prefix}")')
    if page.headings:
        lines.append("")

    for text in page.paragraphs:
        lines.append(f'photon_print("{_esc(text)}")')
    if page.paragraphs:
        lines.append("")

    # Lists
    if page.list_items:
        lines.append("# --- List Items ---")
        arr_items = ", ".join(f'"{_esc(item)}"' for item in page.list_items)
        lines.append(f"let items = [{arr_items}]")
        lines.append("let i = 0")
        lines.append(f"while i < {len(page.list_items)} do")
        lines.append('  photon_print(photon_concat("- ", photon_get(items, i)))')
        lines.append("  i = i + 1")
        lines.append("end")
        lines.append("")

    # Links
    if page.links:
        lines.append("# --- Links ---")
        for href, text in page.links:
            if text:
                lines.append(f'photon_print(photon_concat("{_esc(text)}", " -> {_esc(href)}"))')
        lines.append("")

    # Images (metadata)
    if page.images:
        lines.append("# --- Images ---")
        for src, alt in page.images:
            label = alt if alt else src
            lines.append(f'photon_print("[Image: {_esc(label)}]")')
        lines.append("")

    # Form inputs
    if page.form_inputs:
        lines.append("# --- Form Inputs ---")
        for inp in page.form_inputs:
            name = inp.get("name") or "field"
            placeholder = inp.get("placeholder") or name
            var = _safe_ident(name)
            lines.append(f'let {var} = photon_input("{_esc(placeholder)}: ")')
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CSS → .lux
# ---------------------------------------------------------------------------

def css_to_lux(styles: List[str]) -> str:
    """Translate CSS style blocks into a .lux wavelength-mapping program."""
    lines: List[str] = [
        "# =============================================",
        "# LUXBIN Light Language - CSS Wavelength Styles",
        "# =============================================",
        "",
    ]

    all_rules: List[CSSRule] = []
    for block in styles:
        all_rules.extend(parse_css(block))

    colors = extract_colors(all_rules)

    if colors:
        lines.append("# CSS Color → Wavelength mappings")
        for i, cm in enumerate(colors):
            lines.append(
                f'let color_{i} = {cm.wavelength_nm}  '
                f'# {cm.css_color} → {cm.wavelength_nm}nm'
            )
        lines.append("")
        arr = ", ".join(str(cm.wavelength_nm) for cm in colors)
        lines.append(f"let style_wavelengths = [{arr}]")
        lines.append(f'photon_print("Style wavelengths loaded: {len(colors)} colors")')
    else:
        lines.append('photon_print("No color styles extracted")')

    lines.append("")

    # Emit non-color properties as comments for context
    for rule in all_rules:
        lines.append(f"# {rule.selector}")
        for prop, val in rule.properties:
            lines.append(f"#   {prop}: {val}")
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# JS → .lux
# ---------------------------------------------------------------------------

def js_to_lux(scripts: List[str]) -> str:
    """Translate JavaScript source blocks into .lux programs."""
    lines: List[str] = [
        "# =============================================",
        "# LUXBIN Light Language - JS Translation",
        "# =============================================",
        "",
    ]

    for script in scripts:
        js = parse_js(script)

        # Variables
        for kind, name, val in js.variables:
            lux_kind = "const" if kind == "const" else "let"
            lux_val = _translate_js_value(val)
            lines.append(f"{lux_kind} {_safe_ident(name)} = {lux_val}")

        if js.variables:
            lines.append("")

        # Functions
        for func in js.functions:
            params = ", ".join(func.params)
            lines.append(f"func {_safe_ident(func.name)}({params})")
            body_lines = _translate_js_body(func.body)
            for bl in body_lines:
                lines.append(f"  {bl}")
            lines.append("end")
            lines.append("")

        # Top-level statements
        for stmt in js.statements:
            lines.append(_translate_js_statement(stmt))

    if not any(s.strip() and not s.startswith("#") for s in lines):
        lines.append('photon_print("No JavaScript logic extracted")')

    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    """Escape a string for embedding in a .lux string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def _safe_ident(name: str) -> str:
    """Convert a name to a valid LUXBIN identifier."""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if not name or name[0].isdigit():
        name = "v_" + name
    # Avoid LUXBIN keywords
    keywords = {"let", "const", "func", "return", "if", "then", "else", "end",
                "while", "for", "in", "do", "break", "continue", "true", "false",
                "nil", "and", "or", "not", "import", "export", "quantum",
                "measure", "superpose", "entangle"}
    if name in keywords:
        name = name + "_val"
    return name


def _translate_js_value(val: str) -> str:
    """Translate a JS value expression to .lux."""
    val = val.strip().rstrip(";")
    if val in ("true", "false", "nil", "null"):
        return "true" if val == "true" else ("false" if val == "false" else "nil")
    if val == "undefined" or val == "null":
        return "nil"
    # String
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        inner = val[1:-1]
        return f'"{inner}"'
    # Array
    if val.startswith("["):
        return val  # arrays use same syntax
    # Number or expression
    return val


def _translate_js_statement(stmt: str) -> str:
    """Translate a single JS statement to .lux."""
    stmt = stmt.strip().rstrip(";")
    # console.log(...) → photon_print(...)
    m = re.match(r'console\.log\((.+)\)', stmt)
    if m:
        return f"photon_print({m.group(1)})"
    # alert(...) → photon_print(...)
    m = re.match(r'alert\((.+)\)', stmt)
    if m:
        return f"photon_print({m.group(1)})"
    # prompt(...) → photon_input(...)
    m = re.match(r'prompt\((.+)\)', stmt)
    if m:
        return f"photon_input({m.group(1)})"
    return f"# untranslated: {stmt}"


def _translate_js_body(body: str) -> List[str]:
    """Translate the body of a JS function to .lux lines."""
    out: List[str] = []
    # Split into statements
    stmts = re.split(r';\s*', body)
    for stmt in stmts:
        stmt = stmt.strip()
        if not stmt:
            continue

        # Variable declaration
        m = re.match(r'(var|let|const)\s+(\w+)\s*=\s*(.+)', stmt)
        if m:
            kind = "const" if m.group(1) == "const" else "let"
            out.append(f"{kind} {_safe_ident(m.group(2))} = {_translate_js_value(m.group(3))}")
            continue

        # return
        m = re.match(r'return\s+(.*)', stmt)
        if m:
            out.append(f"return {_translate_js_value(m.group(1))}")
            continue

        # if (simple single-line)
        m = re.match(r'if\s*\((.+?)\)\s*\{(.+?)\}(?:\s*else\s*\{(.+?)\})?', stmt, re.DOTALL)
        if m:
            cond = m.group(1).replace("===", "==").replace("!==", "!=")
            out.append(f"if {cond} then")
            for line in _translate_js_body(m.group(2)):
                out.append(f"  {line}")
            if m.group(3):
                out.append("else")
                for line in _translate_js_body(m.group(3)):
                    out.append(f"  {line}")
            out.append("end")
            continue

        # Generic statement
        out.append(_translate_js_statement(stmt))

    return out
