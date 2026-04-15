"""IR stage: ``list[RawToken]`` + :class:`.BoardProfile` → ``list[SemanticToken]``.

All interpretation is controlled exclusively by the :class:`.BoardProfile`.
This stage must not make assumptions beyond what the profile encodes.
"""

from __future__ import annotations

import re

from .contracts import BoardProfile, RawToken, SemanticToken


def build_ir(raw_tokens: list[RawToken], profile: BoardProfile) -> list[SemanticToken]:
    """Classify each :class:`.RawToken` using *profile* and return a :class:`.SemanticToken` list.

    Rules in *profile* are applied in order; the first matching rule wins.
    If no rule matches, ``profile.default_label`` is used.

    Args:
        raw_tokens: Output of the PARSE stage.
        profile:    Board profile controlling interpretation.

    Returns:
        One :class:`.SemanticToken` per input :class:`.RawToken`, in the same order.
    """
    compiled = [(re.compile(r.pattern), r.label) for r in profile.rules]

    result: list[SemanticToken] = []
    for raw in raw_tokens:
        label = profile.default_label
        for regex, candidate_label in compiled:
            if regex.search(raw.element_id):
                label = candidate_label
                break
        result.append(SemanticToken(raw=raw, label=label))

    return result
