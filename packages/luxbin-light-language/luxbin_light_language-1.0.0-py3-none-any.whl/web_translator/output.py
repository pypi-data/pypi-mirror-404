"""Write .lux files, .json wavelength data, and summary reports."""

import json
import os
from typing import Dict, Any, Optional


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def write_json(data: Dict[str, Any], path: str):
    """Write wavelength JSON data."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def write_lux(source: str, path: str):
    """Write a .lux source file."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)


def write_summary(report: str, path: str):
    """Write a plain-text summary report."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)


def build_summary(
    source: str,
    mode: str,
    content_data: Optional[Dict[str, Any]] = None,
    lux_files: Optional[Dict[str, str]] = None,
) -> str:
    """Build a human-readable summary report."""
    lines = [
        "LUXBIN Web Translator - Summary Report",
        "=" * 40,
        f"Source: {source}",
        f"Mode: {mode}",
        "",
    ]

    if content_data:
        s = content_data.get("summary", {})
        lines.append("Content Translation:")
        lines.append(f"  Title: {content_data.get('source_title', 'N/A')}")
        lines.append(f"  Sections: {s.get('total_sections', 0)}")
        lines.append(f"  Wavelength points: {s.get('total_wavelength_points', 0)}")
        wl_range = s.get("wavelength_range_nm", [0, 0])
        lines.append(f"  Wavelength range: {wl_range[0]}nm - {wl_range[1]}nm")
        lines.append(f"  Total duration: {s.get('total_duration_s', 0):.2f}s")
        lines.append("")

    if lux_files:
        lines.append("Generated .lux files:")
        for name, path in lux_files.items():
            lines.append(f"  {name}: {path}")
        lines.append("")

    lines.append("Done.")
    return "\n".join(lines)
