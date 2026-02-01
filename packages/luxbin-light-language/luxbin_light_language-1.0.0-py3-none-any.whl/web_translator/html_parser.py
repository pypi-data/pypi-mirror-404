"""Parse HTML into structured content."""

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import List, Optional, Tuple


@dataclass
class PageContent:
    title: str = ""
    headings: List[Tuple[int, str]] = field(default_factory=list)  # (level, text)
    paragraphs: List[str] = field(default_factory=list)
    links: List[Tuple[str, str]] = field(default_factory=list)  # (href, text)
    images: List[Tuple[str, str]] = field(default_factory=list)  # (src, alt)
    list_items: List[str] = field(default_factory=list)
    form_inputs: List[dict] = field(default_factory=list)  # {type, name, placeholder, ...}
    scripts: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    all_text: str = ""


class _ContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content = PageContent()
        self._tag_stack: List[str] = []
        self._current_text = ""
        self._in_script = False
        self._in_style = False
        self._script_buf = ""
        self._style_buf = ""
        self._link_href: Optional[str] = None
        self._link_text = ""
        self._all_text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_dict = dict(attrs)

        if tag == "script":
            self._in_script = True
            self._script_buf = ""
        elif tag == "style":
            self._in_style = True
            self._style_buf = ""
        elif tag == "a":
            self._link_href = attr_dict.get("href", "")
            self._link_text = ""
        elif tag == "img":
            self.content.images.append(
                (attr_dict.get("src", ""), attr_dict.get("alt", ""))
            )
        elif tag == "input":
            self.content.form_inputs.append({
                "type": attr_dict.get("type", "text"),
                "name": attr_dict.get("name", ""),
                "placeholder": attr_dict.get("placeholder", ""),
            })
        elif tag == "textarea":
            self.content.form_inputs.append({
                "type": "textarea",
                "name": attr_dict.get("name", ""),
                "placeholder": attr_dict.get("placeholder", ""),
            })
        elif tag == "select":
            self.content.form_inputs.append({
                "type": "select",
                "name": attr_dict.get("name", ""),
            })
        elif tag == "link" and attr_dict.get("rel") == "stylesheet":
            href = attr_dict.get("href", "")
            if href:
                self.content.styles.append(f"/* external: {href} */")

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag == "script":
            self._in_script = False
            stripped = self._script_buf.strip()
            if stripped:
                self.content.scripts.append(stripped)
            self._script_buf = ""
        elif tag == "style":
            self._in_style = False
            stripped = self._style_buf.strip()
            if stripped:
                self.content.styles.append(stripped)
            self._style_buf = ""
        elif tag == "a":
            text = self._link_text.strip()
            if self._link_href is not None:
                self.content.links.append((self._link_href, text))
            self._link_href = None
            self._link_text = ""
        elif tag == "title":
            self.content.title = self._current_text.strip()
            self._current_text = ""
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            text = self._current_text.strip()
            if text:
                self.content.headings.append((level, text))
            self._current_text = ""
        elif tag == "p":
            text = self._current_text.strip()
            if text:
                self.content.paragraphs.append(text)
            self._current_text = ""
        elif tag == "li":
            text = self._current_text.strip()
            if text:
                self.content.list_items.append(text)
            self._current_text = ""

        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def handle_data(self, data: str):
        if self._in_script:
            self._script_buf += data
            return
        if self._in_style:
            self._style_buf += data
            return

        current = self._tag_stack[-1] if self._tag_stack else ""
        if current in ("title", "h1", "h2", "h3", "h4", "h5", "h6", "p", "li"):
            self._current_text += data
        if current == "a":
            self._link_text += data
        # Collect all visible text
        if current not in ("script", "style"):
            stripped = data.strip()
            if stripped:
                self._all_text_parts.append(stripped)

    def finalize(self):
        self.content.all_text = " ".join(self._all_text_parts)


def parse_html(html: str) -> PageContent:
    """Parse raw HTML string into structured PageContent."""
    parser = _ContentParser()
    parser.feed(html)
    parser.finalize()
    return parser.content
