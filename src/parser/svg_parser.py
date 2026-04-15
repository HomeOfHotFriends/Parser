"""SVG parser: converts an SVG file produced by Krita into a :class:`Document`."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union
from urllib.parse import unquote

from .schema import Document, Layer, LayerType

# SVG namespace
_SVG_NS = "http://www.w3.org/2000/svg"

# Regex to extract translate(x, y) from a transform attribute
_TRANSLATE_RE = re.compile(
    r"translate\(\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\)"
)


def _parse_dimension(value: str) -> float:
    """Strip non-numeric suffixes (px, mm, …) and return a float."""
    return float(re.sub(r"[^\d.+-]", "", value))


def _parse_translate(transform: str) -> tuple[float, float]:
    """Return (x, y) from a translate() transform, defaulting to (0, 0)."""
    match = _TRANSLATE_RE.search(transform or "")
    if match:
        return float(match.group(1)), float(match.group(2))
    return 0.0, 0.0


def _classify(group: ET.Element) -> LayerType:
    """Determine the :class:`LayerType` of a ``<g>`` element by its children."""
    text_tags = {f"{{{_SVG_NS}}}text", f"{{{_SVG_NS}}}flowRoot"}
    shape_tags = {
        f"{{{_SVG_NS}}}path",
        f"{{{_SVG_NS}}}rect",
        f"{{{_SVG_NS}}}circle",
        f"{{{_SVG_NS}}}ellipse",
        f"{{{_SVG_NS}}}line",
        f"{{{_SVG_NS}}}polyline",
        f"{{{_SVG_NS}}}polygon",
    }

    for child in group:
        tag = child.tag
        if tag in text_tags:
            return LayerType.TEXT
        if tag in shape_tags:
            return LayerType.SHAPE
        if tag == f"{{{_SVG_NS}}}g":
            return LayerType.GROUP

    return LayerType.UNKNOWN


def _extract_text(group: ET.Element) -> str:
    """Return all text content from a text-type ``<g>`` element."""
    parts: list[str] = []
    for elem in group.iter():
        if elem.text:
            parts.append(elem.text.strip())
        if elem.tail:
            parts.append(elem.tail.strip())
    return " ".join(p for p in parts if p)


def _parse_group(group: ET.Element) -> Layer:
    """Convert a ``<g>`` element into a :class:`Layer`."""
    raw_id = group.get("id", "")
    # Krita URL-encodes spaces as %20; decode for the human-readable name
    name = unquote(raw_id)

    transform = group.get("transform", "")
    x, y = _parse_translate(transform)
    layer_type = _classify(group)

    text: str | None = None
    children: list[Layer] = []

    if layer_type == LayerType.TEXT:
        text = _extract_text(group)
    elif layer_type == LayerType.GROUP:
        children = [
            _parse_group(child)
            for child in group
            if child.tag == f"{{{_SVG_NS}}}g"
        ]

    return Layer(
        id=raw_id,
        name=name,
        layer_type=layer_type,
        x=x,
        y=y,
        text=text,
        children=children,
    )


def parse_svg(source: Union[str, Path]) -> Document:
    """Parse a Krita-exported SVG file and return a :class:`Document`.

    Args:
        source: Path to the ``.svg`` file.

    Returns:
        A :class:`Document` containing all top-level layers.
    """
    tree = ET.parse(str(source))
    root = tree.getroot()

    width = _parse_dimension(root.get("width", "0"))
    height = _parse_dimension(root.get("height", "0"))

    layers = [
        _parse_group(child)
        for child in root
        if child.tag == f"{{{_SVG_NS}}}g"
    ]

    return Document(width=width, height=height, layers=layers)
