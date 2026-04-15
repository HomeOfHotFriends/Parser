"""Minimal extraction schema for SVG-based (Krita) parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LayerType(str, Enum):
    """The kind of content a layer contains."""

    TEXT = "text"
    SHAPE = "shape"
    GROUP = "group"
    UNKNOWN = "unknown"


@dataclass
class Layer:
    """A single layer extracted from an SVG ``<g>`` element.

    Attributes:
        id:         The raw ``id`` attribute on the ``<g>`` element.
        name:       Human-readable layer name (decoded from ``id``).
        layer_type: Content classification.
        x:          Left edge in document coordinates (from ``translate``).
        y:          Top edge in document coordinates (from ``translate``).
        text:       Plain-text content for ``LayerType.TEXT`` layers.
        children:   Nested layers for ``LayerType.GROUP`` layers.
    """

    id: str
    name: str
    layer_type: LayerType
    x: float = 0.0
    y: float = 0.0
    text: Optional[str] = None
    children: list[Layer] = field(default_factory=list)


@dataclass
class Document:
    """The top-level SVG document.

    Attributes:
        width:  Canvas width in user units (from ``<svg width>``).
        height: Canvas height in user units (from ``<svg height>``).
        layers: Top-level layers in z-order (bottom → top).
    """

    width: float
    height: float
    layers: list[Layer] = field(default_factory=list)
