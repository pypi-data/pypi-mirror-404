"""CLI entry point for the LUXBIN Web Translator."""

import argparse
import os
import sys

from web_translator.fetcher import fetch
from web_translator.html_parser import parse_html
from web_translator.content_to_lll import content_to_wavelengths
from web_translator.code_to_lux import html_to_lux, css_to_lux, js_to_lux
from web_translator.output import write_json, write_lux, write_summary, build_summary


def translate(source: str, mode: str, output_dir: str):
    """Run the full translation pipeline."""
    os.makedirs(output_dir, exist_ok=True)

    # Fetch
    print(f"Fetching: {source}")
    result = fetch(source)

    # Parse HTML
    page = parse_html(result.html)
    print(f"Parsed: title={page.title!r}, "
          f"{len(page.headings)} headings, {len(page.paragraphs)} paragraphs, "
          f"{len(page.links)} links, {len(page.scripts)} scripts, {len(page.styles)} styles")

    content_data = None
    lux_files = {}

    # Mode: content
    if mode in ("content", "both"):
        print("Generating wavelength data...")
        content_data = content_to_wavelengths(page)
        json_path = os.path.join(output_dir, "page_content.json")
        write_json(content_data, json_path)
        print(f"  -> {json_path}")

    # Mode: code
    if mode in ("code", "both"):
        print("Translating to .lux...")

        # HTML → .lux
        lux_src = html_to_lux(page)
        lux_path = os.path.join(output_dir, "page.lux")
        write_lux(lux_src, lux_path)
        lux_files["page.lux"] = lux_path
        print(f"  -> {lux_path}")

        # CSS → .lux
        if page.styles:
            css_src = css_to_lux(page.styles)
            css_path = os.path.join(output_dir, "page_styles.lux")
            write_lux(css_src, css_path)
            lux_files["page_styles.lux"] = css_path
            print(f"  -> {css_path}")

        # JS → .lux
        if page.scripts:
            js_src = js_to_lux(page.scripts)
            js_path = os.path.join(output_dir, "page_scripts.lux")
            write_lux(js_src, js_path)
            lux_files["page_scripts.lux"] = js_path
            print(f"  -> {js_path}")

    # Summary
    summary = build_summary(source, mode, content_data, lux_files)
    summary_path = os.path.join(output_dir, "summary.txt")
    write_summary(summary, summary_path)
    print(f"  -> {summary_path}")
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        prog="web_translator",
        description="LUXBIN Web-to-Light-Language Translator",
    )
    sub = parser.add_subparsers(dest="command")

    tr = sub.add_parser("translate", help="Translate a web page or HTML file")
    tr.add_argument("source", help="URL or local HTML file path")
    tr.add_argument("--mode", choices=["content", "code", "both"], default="both",
                     help="Translation mode (default: both)")
    tr.add_argument("--output", "-o", default="./output",
                     help="Output directory (default: ./output)")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "translate":
        translate(args.source, args.mode, args.output)


if __name__ == "__main__":
    main()
