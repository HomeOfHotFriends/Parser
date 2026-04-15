"""SVG → token compiler pipeline (Phase 1: Python implementation).

Public API
----------
parse(source)               SVG file → list[RawToken]
build_ir(tokens, profile)   list[RawToken] + BoardProfile → list[SemanticToken]
emit_json(tokens)           list[SemanticToken] → JSON string
"""

from .contracts import BoardProfile, LabelRule, RawToken, SemanticToken
from .emit import emit_json
from .ir import build_ir
from .parse import parse

__all__ = [
    "BoardProfile",
    "LabelRule",
    "RawToken",
    "SemanticToken",
    "parse",
    "build_ir",
    "emit_json",
]
