# Parser

SVG → token compiler pipeline.  Phase 1 is implemented in Python; the core will be ported to C++ at Phase 3 for Godot/GDExtension integration.

## Pipeline

```
PARSE  →  IR  →  EMIT
```

| Stage | Input | Output | Rules |
|-------|-------|--------|-------|
| `parse()` | `.svg` file | `list[RawToken]` | Extraction only — no interpretation |
| `build_ir()` | `list[RawToken]` + `BoardProfile` | `list[SemanticToken]` | Interpretation controlled exclusively by profile |
| `emit_json()` | `list[SemanticToken]` | JSON string | Serialisation only |

## Data contracts

```python
@dataclass(frozen=True)
class RawToken:
    text: str        # raw text content of <text> element
    x: float         # x coordinate in document units
    y: float         # y coordinate in document units
    element_id: str  # SVG id attribute (empty string if absent)

@dataclass(frozen=True)
class LabelRule:
    pattern: str  # regex matched against RawToken.element_id
    label: str    # assigned when pattern matches

@dataclass
class BoardProfile:
    name: str
    rules: list[LabelRule]   # evaluated in order; first match wins
    default_label: str       # fallback when no rule matches

@dataclass(frozen=True)
class SemanticToken:
    raw: RawToken
    label: str  # assigned by BoardProfile
```

## Usage

```python
from parser import parse, build_ir, emit_json, BoardProfile, LabelRule

profile = BoardProfile(
    name="card",
    rules=[
        LabelRule(pattern=r"title", label="title"),
        LabelRule(pattern=r"cost",  label="cost"),
        LabelRule(pattern=r"body",  label="body"),
    ],
)

tokens = build_ir(parse("card.svg"), profile)
print(emit_json(tokens))
```

## Language note

Phase 1 (PARSE + IR) is Python for fast iteration.  The data contracts (`RawToken`, `SemanticToken`, `BoardProfile`) are intentionally plain data — when the pipeline is ported to C++ at Phase 3, each contract becomes a struct and the port is a translation, not a redesign.