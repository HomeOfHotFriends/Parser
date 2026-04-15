"""Tests for the three-stage pipeline: PARSE → IR → EMIT."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from parser import BoardProfile, LabelRule, RawToken, SemanticToken, build_ir, emit_json, parse

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SVG_FIXTURE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
      <text id="card-title" x="100" y="50">Storm Drake</text>
      <text id="card-cost" x="700" y="50">5</text>
      <text id="card-body" x="100" y="300">Deal 3 damage to any target.</text>
      <g transform="translate(0, 400)">
        <text id="card-flavour">The sky splits when it roars.</text>
      </g>
    </svg>""")


@pytest.fixture
def svg_file(tmp_path: Path) -> Path:
    path = tmp_path / "card.svg"
    path.write_text(SVG_FIXTURE, encoding="utf-8")
    return path


@pytest.fixture
def default_profile() -> BoardProfile:
    return BoardProfile(
        name="test",
        rules=[
            LabelRule(pattern=r"title", label="title"),
            LabelRule(pattern=r"cost", label="cost"),
            LabelRule(pattern=r"body", label="body"),
            LabelRule(pattern=r"flavour", label="flavour"),
        ],
        default_label="unknown",
    )


# ---------------------------------------------------------------------------
# PARSE stage
# ---------------------------------------------------------------------------

class TestParse:
    def test_token_count(self, svg_file):
        tokens = parse(svg_file)
        assert len(tokens) == 4

    def test_token_type(self, svg_file):
        tokens = parse(svg_file)
        assert all(isinstance(t, RawToken) for t in tokens)

    def test_text_extraction(self, svg_file):
        tokens = parse(svg_file)
        assert tokens[0].text == "Storm Drake"
        assert tokens[1].text == "5"
        assert tokens[2].text == "Deal 3 damage to any target."
        assert tokens[3].text == "The sky splits when it roars."

    def test_position_from_attributes(self, svg_file):
        tokens = parse(svg_file)
        assert tokens[0].x == 100.0
        assert tokens[0].y == 50.0
        assert tokens[1].x == 700.0
        assert tokens[1].y == 50.0

    def test_element_id(self, svg_file):
        tokens = parse(svg_file)
        assert tokens[0].element_id == "card-title"
        assert tokens[1].element_id == "card-cost"
        assert tokens[3].element_id == "card-flavour"

    def test_element_without_position_defaults_to_zero(self, svg_file):
        tokens = parse(svg_file)
        # card-flavour has no x/y attrs and no transform on the <text> itself
        assert tokens[3].x == 0.0
        assert tokens[3].y == 0.0

    def test_raw_token_is_immutable(self, svg_file):
        tokens = parse(svg_file)
        with pytest.raises((AttributeError, TypeError)):
            tokens[0].text = "mutated"  # type: ignore[misc]  # frozen=True

    def test_empty_svg_returns_no_tokens(self, tmp_path):
        svg = tmp_path / "empty.svg"
        svg.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"/>',
            encoding="utf-8",
        )
        assert parse(svg) == []


# ---------------------------------------------------------------------------
# IR stage
# ---------------------------------------------------------------------------

class TestBuildIR:
    def test_output_length_matches_input(self, svg_file, default_profile):
        raw = parse(svg_file)
        semantic = build_ir(raw, default_profile)
        assert len(semantic) == len(raw)

    def test_label_assignment(self, svg_file, default_profile):
        raw = parse(svg_file)
        semantic = build_ir(raw, default_profile)
        assert [t.label for t in semantic] == ["title", "cost", "body", "flavour"]

    def test_default_label_fallback(self):
        raw = [RawToken(text="?", x=0.0, y=0.0, element_id="unrecognised")]
        profile = BoardProfile(name="p", rules=[], default_label="misc")
        semantic = build_ir(raw, profile)
        assert semantic[0].label == "misc"

    def test_first_rule_wins(self):
        raw = [RawToken(text="x", x=0.0, y=0.0, element_id="card-title-large")]
        profile = BoardProfile(
            name="p",
            rules=[
                LabelRule(pattern=r"title", label="title"),
                LabelRule(pattern=r"large", label="large"),
            ],
        )
        semantic = build_ir(raw, profile)
        assert semantic[0].label == "title"

    def test_raw_preserved_in_semantic(self, svg_file, default_profile):
        raw = parse(svg_file)
        semantic = build_ir(raw, default_profile)
        assert semantic[0].raw is raw[0]

    def test_semantic_token_is_immutable(self, svg_file, default_profile):
        raw = parse(svg_file)
        semantic = build_ir(raw, default_profile)
        with pytest.raises((AttributeError, TypeError)):
            semantic[0].label = "mutated"  # type: ignore[misc]  # frozen=True

    def test_empty_input_returns_empty(self, default_profile):
        assert build_ir([], default_profile) == []


# ---------------------------------------------------------------------------
# EMIT stage
# ---------------------------------------------------------------------------

class TestEmitJson:
    def test_valid_json(self, svg_file, default_profile):
        semantic = build_ir(parse(svg_file), default_profile)
        parsed = json.loads(emit_json(semantic))
        assert isinstance(parsed, list)

    def test_length(self, svg_file, default_profile):
        semantic = build_ir(parse(svg_file), default_profile)
        assert len(json.loads(emit_json(semantic))) == 4

    def test_fields_present(self, svg_file, default_profile):
        semantic = build_ir(parse(svg_file), default_profile)
        first = json.loads(emit_json(semantic))[0]
        assert "label" in first
        assert "raw" in first
        assert "text" in first["raw"]
        assert "x" in first["raw"]
        assert "y" in first["raw"]
        assert "element_id" in first["raw"]

    def test_label_values(self, svg_file, default_profile):
        semantic = build_ir(parse(svg_file), default_profile)
        output = json.loads(emit_json(semantic))
        assert output[0]["label"] == "title"
        assert output[1]["label"] == "cost"

    def test_compact_output(self, svg_file, default_profile):
        semantic = build_ir(parse(svg_file), default_profile)
        compact = emit_json(semantic, indent=None)
        assert "\n" not in compact

    def test_empty_input(self):
        assert emit_json([]) == "[]"


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_full_pipeline(self, svg_file, default_profile):
        output = json.loads(emit_json(build_ir(parse(svg_file), default_profile)))
        assert output[0]["raw"]["text"] == "Storm Drake"
        assert output[0]["label"] == "title"
        assert output[1]["raw"]["text"] == "5"
        assert output[1]["label"] == "cost"
        assert output[2]["raw"]["text"] == "Deal 3 damage to any target."
        assert output[2]["label"] == "body"
        assert output[3]["raw"]["text"] == "The sky splits when it roars."
        assert output[3]["label"] == "flavour"
