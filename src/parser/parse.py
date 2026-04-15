"""PARSE stage: SVG file → ``list[RawToken]``.

Only extraction happens here.  No interpretation, no profile.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union

from .contracts import RawToken

_SVG_NS = "http://www.w3.org/2000/svg"
_TEXT_TAG = f"{{{_SVG_NS}}}text"

_TRANSLATE_RE = re.compile(
    r"translate\(\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\)"
)


def _parse_coord(value: str | None, default: float = 0.0) -> float:
    """Parse a numeric SVG attribute value, stripping unit suffixes."""
    if not value:
        return default
    try:
        return float(re.sub(r"[a-zA-Z%]", "", value))
    except ValueError:
        return default


def _parse_translate(transform: str | None) -> tuple[float, float]:
    """Extract ``(dx, dy)`` from a ``translate()`` transform attribute."""
    match = _TRANSLATE_RE.search(transform or "")
    if match:
        return float(match.group(1)), float(match.group(2))
    return 0.0, 0.0


def _collect_text(element: ET.Element) -> str:
    """Return all text content from *element*, collapsing internal whitespace."""
    parts: list[str] = []
    for node in element.iter():
        if node.text:
            parts.append(node.text.strip())
        if node.tail:
            parts.append(node.tail.strip())
    return " ".join(p for p in parts if p)


def parse(source: Union[str, Path]) -> list[RawToken]:
    """Parse *source* SVG and return one :class:`.RawToken` per ``<text>`` element.

    Position is taken from the element's ``x``/``y`` attributes plus any
    ``translate()`` on the element's own ``transform`` attribute.  Parent
    transforms are not accumulated in Phase 1.

    Args:
        source: Path to the ``.svg`` file.

    Returns:
        List of :class:`.RawToken`, one per ``<text>`` element found, in
        document order.
    """
    tree = ET.parse(str(source))
    root = tree.getroot()

    tokens: list[RawToken] = []
    for elem in root.iter(_TEXT_TAG):
        dx, dy = _parse_translate(elem.get("transform"))
        x = _parse_coord(elem.get("x")) + dx
        y = _parse_coord(elem.get("y")) + dy
        tokens.append(
            RawToken(
                text=_collect_text(elem),
                x=x,
                y=y,
                element_id=elem.get("id", ""),
            )
        )

    return tokens
