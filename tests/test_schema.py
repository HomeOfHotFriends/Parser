"""Tests for the minimal SVG extraction schema and parser."""

from __future__ import annotations

import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from parser.schema import Document, Layer, LayerType
from parser.svg_parser import _parse_translate, _classify, _parse_group, parse_svg


# ---------------------------------------------------------------------------
# Schema unit tests
# ---------------------------------------------------------------------------

class TestLayerDefaults:
    def test_layer_default_position(self):
        layer = Layer(id="bg", name="bg", layer_type=LayerType.SHAPE)
        assert layer.x == 0.0
        assert layer.y == 0.0

    def test_layer_text_field_default_none(self):
        layer = Layer(id="t", name="t", layer_type=LayerType.TEXT)
        assert layer.text is None

    def test_layer_children_default_empty(self):
        layer = Layer(id="g", name="g", layer_type=LayerType.GROUP)
        assert layer.children == []


class TestDocumentDefaults:
    def test_document_layers_default_empty(self):
        doc = Document(width=800.0, height=600.0)
        assert doc.layers == []

    def test_document_dimensions(self):
        doc = Document(width=1920.0, height=1080.0)
        assert doc.width == 1920.0
        assert doc.height == 1080.0


# ---------------------------------------------------------------------------
# Parser helper unit tests
# ---------------------------------------------------------------------------

class TestParseTranslate:
    def test_basic_translate(self):
        assert _parse_translate("translate(10, 20)") == (10.0, 20.0)

    def test_float_translate(self):
        assert _parse_translate("translate(1.5, 3.75)") == (1.5, 3.75)

    def test_no_transform(self):
        assert _parse_translate("") == (0.0, 0.0)

    def test_none_treated_as_empty(self):
        assert _parse_translate(None) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Integration test using an in-memory SVG
# ---------------------------------------------------------------------------

SVG_FIXTURE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
      <g id="background" transform="translate(0, 0)">
        <rect x="0" y="0" width="800" height="600"/>
      </g>
      <g id="title%20text" transform="translate(100, 50)">
        <text>Hello World</text>
      </g>
      <g id="grouped_items" transform="translate(0, 0)">
        <g id="item1">
          <path d="M 0 0 L 10 10"/>
        </g>
      </g>
    </svg>
""")


@pytest.fixture
def svg_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.svg"
    path.write_text(SVG_FIXTURE, encoding="utf-8")
    return path


class TestParseSvg:
    def test_document_dimensions(self, svg_file):
        doc = parse_svg(svg_file)
        assert doc.width == 800.0
        assert doc.height == 600.0

    def test_layer_count(self, svg_file):
        doc = parse_svg(svg_file)
        assert len(doc.layers) == 3

    def test_shape_layer(self, svg_file):
        doc = parse_svg(svg_file)
        bg = doc.layers[0]
        assert bg.id == "background"
        assert bg.name == "background"
        assert bg.layer_type == LayerType.SHAPE
        assert bg.x == 0.0
        assert bg.y == 0.0

    def test_text_layer(self, svg_file):
        doc = parse_svg(svg_file)
        title = doc.layers[1]
        assert title.id == "title%20text"
        assert title.name == "title text"  # URL-decoded
        assert title.layer_type == LayerType.TEXT
        assert title.x == 100.0
        assert title.y == 50.0
        assert title.text == "Hello World"

    def test_group_layer(self, svg_file):
        doc = parse_svg(svg_file)
        group = doc.layers[2]
        assert group.layer_type == LayerType.GROUP
        assert len(group.children) == 1
        assert group.children[0].id == "item1"
