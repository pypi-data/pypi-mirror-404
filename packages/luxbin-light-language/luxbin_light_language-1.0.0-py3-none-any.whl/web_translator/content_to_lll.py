"""Mode 1: Convert page content to wavelength sequences using LuxbinLightConverter."""

import sys
import os
from typing import Dict, Any, List

# Add parent so we can import the converter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from luxbin_light_converter import LuxbinLightConverter
from web_translator.html_parser import PageContent


def content_to_wavelengths(page: PageContent) -> Dict[str, Any]:
    """Convert structured page content into LUXBIN wavelength data.

    Returns a JSON-serialisable dict with per-section wavelength sequences
    and a combined light-show.
    """
    converter = LuxbinLightConverter()
    sections: List[Dict[str, Any]] = []

    # Title
    if page.title:
        show = converter.create_grammar_light_show(page.title)
        sections.append(_section("title", page.title, show))

    # Headings
    for level, text in page.headings:
        show = converter.create_grammar_light_show(text)
        sec = _section(f"h{level}", text, show)
        sec["heading_level"] = level
        sections.append(sec)

    # Paragraphs
    for text in page.paragraphs:
        show = converter.create_grammar_light_show(text)
        sections.append(_section("paragraph", text, show))

    # List items
    if page.list_items:
        combined = " ".join(page.list_items)
        show = converter.create_grammar_light_show(combined)
        sec = _section("list", combined, show)
        sec["items"] = page.list_items
        sections.append(sec)

    # Links (text only)
    for href, text in page.links:
        if not text:
            continue
        show = converter.create_grammar_light_show(text)
        sec = _section("link", text, show)
        sec["href"] = href
        sections.append(sec)

    # Full-page combined
    full_show = None
    if page.all_text:
        # Limit to first 2000 chars to keep output reasonable
        snippet = page.all_text[:2000]
        full_show = converter.create_grammar_light_show(snippet)

    # Build wavelength summary
    all_wavelengths: List[float] = []
    for sec in sections:
        all_wavelengths.extend(sec.get("wavelengths", []))

    return {
        "source_title": page.title,
        "sections": sections,
        "full_page_light_show": _slim_show(full_show) if full_show else None,
        "summary": {
            "total_sections": len(sections),
            "total_wavelength_points": len(all_wavelengths),
            "wavelength_range_nm": [
                round(min(all_wavelengths), 1) if all_wavelengths else 0,
                round(max(all_wavelengths), 1) if all_wavelengths else 0,
            ],
            "total_duration_s": sum(
                s.get("duration_s", 0) for s in sections
            ),
        },
    }


def _section(kind: str, text: str, show: Dict[str, Any]) -> Dict[str, Any]:
    wavelengths = [item["wavelength_nm"] for item in show["light_sequence"]]
    return {
        "type": kind,
        "text": text,
        "wavelengths": wavelengths,
        "duration_s": show["total_duration"],
        "character_count": show["total_characters"],
    }


def _slim_show(show: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact version of a light show for JSON output."""
    return {
        "total_characters": show["total_characters"],
        "total_duration_s": show["total_duration"],
        "wavelength_sequence": [
            {"char": item["character"], "nm": item["wavelength_nm"]}
            for item in show["light_sequence"]
        ],
    }
