"""Frozen data contracts for the SVG → token pipeline.

These three types — ``RawToken``, ``SemanticToken``, ``BoardProfile`` — are the
stable interface between pipeline stages.  They are intentionally plain data
so that a future C++ port is a struct translation, not a redesign.

Pipeline::

    PARSE  : SVG file            → list[RawToken]       (extraction only)
    IR     : list[RawToken]      → list[SemanticToken]  (interpretation via BoardProfile)
    EMIT   : list[SemanticToken] → JSON string          (serialisation)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawToken:
    """A single text element extracted from SVG.  Extraction only — no interpretation.

    Attributes:
        text:       Raw text content of the ``<text>`` element.
        x:          X coordinate in document units.
        y:          Y coordinate in document units.
        element_id: The ``id`` attribute of the source SVG element (empty string if absent).
    """

    text: str
    x: float
    y: float
    element_id: str


@dataclass(frozen=True)
class LabelRule:
    """A single classification rule inside a :class:`BoardProfile`.

    Attributes:
        pattern: A regex pattern matched (search) against :attr:`RawToken.element_id`.
        label:   The semantic label assigned when the pattern matches.
    """

    pattern: str
    label: str


@dataclass
class BoardProfile:
    """Controls how :class:`RawToken` values are interpreted into :class:`SemanticToken` values.

    Rules are evaluated in order; the first match wins.  If no rule matches,
    :attr:`default_label` is used.

    Attributes:
        name:          Human-readable profile name.
        rules:         Ordered list of :class:`LabelRule` objects.
        default_label: Fallback label when no rule matches.
    """

    name: str
    rules: list[LabelRule] = field(default_factory=list)
    default_label: str = "unknown"


@dataclass(frozen=True)
class SemanticToken:
    """An interpreted token.  Interpretation is controlled exclusively by :class:`BoardProfile`.

    Attributes:
        raw:   The originating :class:`RawToken`.
        label: Semantic label assigned by the IR stage.
    """

    raw: RawToken
    label: str
