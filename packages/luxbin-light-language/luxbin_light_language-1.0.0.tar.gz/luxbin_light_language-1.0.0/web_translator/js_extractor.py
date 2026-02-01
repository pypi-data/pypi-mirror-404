"""Extract and parse JavaScript logic from HTML pages."""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSFunction:
    name: str
    params: List[str]
    body: str


@dataclass
class JSContent:
    functions: List[JSFunction] = field(default_factory=list)
    variables: List[tuple] = field(default_factory=list)  # (kind, name, value)
    statements: List[str] = field(default_factory=list)  # raw statements not in functions


def parse_js(js_text: str) -> JSContent:
    """Parse JavaScript source into structured components."""
    content = JSContent()

    # Strip single-line comments
    cleaned = re.sub(r'//.*', '', js_text)
    # Strip multi-line comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Extract function declarations and track their spans
    func_pattern = re.compile(
        r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', re.DOTALL
    )
    func_spans = []
    for m in func_pattern.finditer(cleaned):
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(',') if p.strip()]
        body_start = m.end() - 1
        body = _extract_brace_block(cleaned, body_start)
        body_end = body_start + len(body) + 2  # account for braces
        func_spans.append((m.start(), body_end))
        content.functions.append(JSFunction(name=name, params=params, body=body))

    def _inside_function(pos: int) -> bool:
        return any(start <= pos < end for start, end in func_spans)

    # Extract top-level variable declarations only
    var_pattern = re.compile(r'\b(var|let|const)\s+(\w+)\s*=\s*([^;\n]+)')
    for m in var_pattern.finditer(cleaned):
        if _inside_function(m.start()):
            continue
        kind, name, val = m.group(1), m.group(2), m.group(3).strip()
        content.variables.append((kind, name, val))

    # Collect top-level statements (console.log, alert, etc.)
    stmt_pattern = re.compile(r'^[ \t]*((?:console\.log|alert|document\.\w+)\s*\([^)]*\))\s*;?', re.MULTILINE)
    for m in stmt_pattern.finditer(cleaned):
        if _inside_function(m.start()):
            continue
        content.statements.append(m.group(1).strip())

    return content


def _extract_brace_block(text: str, start: int) -> str:
    """Extract content between balanced braces starting at text[start] == '{'."""
    if start >= len(text) or text[start] != '{':
        return ""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i].strip()
        i += 1
    return text[start + 1:].strip()
