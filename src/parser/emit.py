"""EMIT stage: ``list[SemanticToken]`` → JSON string."""

from __future__ import annotations

import json
from dataclasses import asdict

from .contracts import SemanticToken


def emit_json(semantic_tokens: list[SemanticToken], *, indent: int | None = 2) -> str:
    """Serialise *semantic_tokens* to a JSON string.

    Args:
        semantic_tokens: Output of the IR stage.
        indent:          JSON indentation level; ``None`` for compact output.

    Returns:
        A JSON array string, one object per token.
    """
    return json.dumps([asdict(t) for t in semantic_tokens], indent=indent)
