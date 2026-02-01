"""Fetch web pages by URL or read local HTML files."""

import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FetchResult:
    html: str
    source: str  # URL or file path
    content_type: str = "text/html"
    encoding: str = "utf-8"


def fetch(source: str, timeout: int = 15) -> FetchResult:
    """Fetch HTML from a URL or local file path.

    Args:
        source: A URL (http/https) or local file path.
        timeout: Request timeout in seconds (URLs only).

    Returns:
        FetchResult with raw HTML and metadata.
    """
    if source.startswith(("http://", "https://")):
        return _fetch_url(source, timeout)
    return _read_file(source)


def _fetch_url(url: str, timeout: int) -> FetchResult:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "LuxbinWebTranslator/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "text/html")
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].split(";")[0].strip()
        raw = resp.read()
        html = raw.decode(encoding, errors="replace")
    return FetchResult(html=html, source=url, content_type=content_type, encoding=encoding)


def _read_file(path: str) -> FetchResult:
    path = os.path.abspath(path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    return FetchResult(html=html, source=path)
