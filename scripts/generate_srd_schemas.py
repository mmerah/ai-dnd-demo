from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# --- Streaming helpers -----------------------------------------------------


def iter_array_items(path: Path, max_items: int = 5) -> list[Any]:
    """Stream-parse the first N items of a top-level JSON array without
    reading the full file. Returns up to max_items parsed Python objects.

    The files in docs/5e-database-snippets/src/2014 are arrays of objects.
    """
    dec = json.JSONDecoder()
    items: list[Any] = []
    buf = ""
    with path.open("r", encoding="utf-8") as f:
        # Read until we see the opening '['
        while True:
            ch = f.read(1)
            if not ch:
                break
            if ch.isspace():
                continue
            buf = ch
            break

        if not buf or buf[0] != "[":
            raise ValueError(f"Expected top-level array in {path}")

        # Now parse successive items separated by commas, until ']' or max_items.
        idx = 1  # past the '['
        while len(items) < max_items:
            # skip whitespace and commas
            while True:
                if idx >= len(buf):
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    buf += chunk
                ch = buf[idx]
                if ch.isspace() or ch == ",":
                    idx += 1
                    continue
                break

            if idx >= len(buf):
                break
            if buf[idx] == "]":
                # end of array
                break

            # Try to raw-decode an item starting at idx; if incomplete, read more.
            while True:
                try:
                    obj, end = dec.raw_decode(buf, idx)
                    items.append(obj)
                    idx = end
                    break
                except json.JSONDecodeError:
                    chunk = f.read(8192)
                    if not chunk:
                        raise
                    buf += chunk

    return items


# --- Type inference --------------------------------------------------------

Schema = dict[str, Any]


def schema_of(value: Any) -> Schema:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    # Distinguish integer vs float for tighter typing
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {"type": "unknown"}}
        # Merge item schemas
        item_schema: Schema | None = None
        for v in value:
            s = schema_of(v)
            item_schema = merge_schema(item_schema, s)
        return {"type": "array", "items": item_schema or {"type": "unknown"}}
    if isinstance(value, dict):
        props: dict[str, Schema] = {}
        required: dict[str, int] = {}
        for k, v in value.items():
            props[k] = schema_of(v)
            required[k] = 1
        return {"type": "object", "properties": props, "required_counts": required}
    return {"type": "unknown"}


def merge_schema(a: Schema | None, b: Schema | None) -> Schema:
    if a is None:
        return b or {"type": "unknown"}
    if b is None:
        return a

    # Handle unions
    variants = a["anyOf"] if a.get("anyOf") else [a]
    bvars = b["anyOf"] if b.get("anyOf") else [b]

    # If types match, merge recursively
    merged_candidates: list[Schema] = []
    for va in variants:
        matched = False
        for vb in list(bvars):
            if va.get("type") == vb.get("type") == "object":
                merged_candidates.append(merge_object(va, vb))
                bvars.remove(vb)
                matched = True
                break
            if va.get("type") == vb.get("type") == "array":
                merged_candidates.append(
                    {
                        "type": "array",
                        "items": merge_schema(va.get("items"), vb.get("items")),
                    }
                )
                bvars.remove(vb)
                matched = True
                break
            # Numeric widening: integer + number -> number
            if {va.get("type"), vb.get("type")} == {"integer", "number"}:
                merged_candidates.append({"type": "number"})
                bvars.remove(vb)
                matched = True
                break
            if va.get("type") == vb.get("type"):
                merged_candidates.append(va)
                bvars.remove(vb)
                matched = True
                break
        if not matched:
            merged_candidates.append(va)

    merged_candidates.extend(bvars)
    # Deduplicate by type signature
    dedup: list[Schema] = []
    seen = set()
    for s in merged_candidates:
        key = json.dumps(signature_of(s), sort_keys=True)
        if key not in seen:
            seen.add(key)
            dedup.append(s)

    if len(dedup) == 1:
        return dedup[0]
    return {"anyOf": dedup}


def merge_object(a: Schema, b: Schema) -> Schema:
    props: dict[str, Schema] = {}
    req_counts: dict[str, int] = {}
    for k in set(a.get("properties", {}).keys()) | set(b.get("properties", {}).keys()):
        props[k] = merge_schema(a.get("properties", {}).get(k), b.get("properties", {}).get(k))
        req_counts[k] = a.get("required_counts", {}).get(k, 0) + b.get("required_counts", {}).get(k, 0)
    return {"type": "object", "properties": props, "required_counts": req_counts}


def signature_of(s: Schema) -> Any:
    if s.get("anyOf"):
        return {"anyOf": [signature_of(x) for x in s["anyOf"]]}
    t = s.get("type")
    if t in {"string", "number", "integer", "boolean", "null", "unknown"}:
        return t
    if t == "array":
        return {"array": signature_of(s.get("items", {"type": "unknown"}))}
    if t == "object":
        return {"object": {k: signature_of(v) for k, v in sorted(s.get("properties", {}).items())}}
    return "unknown"


# --- Rendering to TypeScript-ish types ------------------------------------


def to_ts(name: str, schema: Schema, sample_count: int, indent: int = 0) -> list[str]:
    sp = "  " * indent
    lines: list[str] = []

    if schema.get("anyOf"):
        parts: list[str] = []
        for variant in schema["anyOf"]:
            nested = to_ts_inline(variant, sample_count, indent)
            parts.append(nested)
        lines.append(f"{sp}{name}: (" + " | ".join(parts) + ");")
        return lines

    t = schema.get("type")
    if t == "object":
        lines.append(f"{sp}{name}: {{")
        props: dict[str, Schema] = schema.get("properties", {})
        req_counts: dict[str, int] = schema.get("required_counts", {})
        for k in sorted(props.keys()):
            opt = "?" if req_counts.get(k, 0) < sample_count else ""
            sub = to_ts(f"{k}{opt}", props[k], sample_count, indent + 1)
            lines.extend(sub)
        lines.append(f"{sp}}};")
        return lines
    if t == "array":
        item = to_ts_inline(schema.get("items", {"type": "unknown"}), sample_count, indent)
        lines.append(f"{sp}{name}: {item}[];")
        return lines
    # primitives
    prim = ts_primitive(t)
    lines.append(f"{sp}{name}: {prim};")
    return lines


def to_ts_inline(schema: Schema, sample_count: int, indent: int) -> str:
    if schema.get("anyOf"):
        return "(" + " | ".join(to_ts_inline(s, sample_count, indent) for s in schema["anyOf"]) + ")"
    t = schema.get("type")
    if t == "object":
        # Inline object
        props: dict[str, Schema] = schema.get("properties", {})
        req_counts: dict[str, int] = schema.get("required_counts", {})
        inner: list[str] = []
        for k in sorted(props.keys()):
            opt = "?" if req_counts.get(k, 0) < sample_count else ""
            sub_lines = to_ts(f"{k}{opt}", props[k], sample_count, indent + 1)
            inner.extend(sub_lines)
        # Convert lines to one inline block if small, else multiline
        if len(inner) <= 3 and all("{" not in ln for ln in inner):
            # Compact
            compact = " ".join(ln.strip() for ln in inner)
            return "{" + compact + " }"
        else:
            # Multiline inline
            return "{\n" + "\n".join(inner) + "\n}"
    if t == "array":
        return to_ts_inline(schema.get("items", {"type": "unknown"}), sample_count, indent) + "[]"
    return ts_primitive(t)


def ts_primitive(t: str | None) -> str:
    return {
        "string": "string",
        "number": "number",
        "integer": "number",
        "boolean": "boolean",
        "null": "null",
        "unknown": "unknown",
        None: "unknown",
    }.get(t, "unknown")


# --- Pydantic rendering ----------------------------------------------------


def pyd_primitive(t: str | None) -> str:
    return {
        "string": "str",
        "integer": "int",
        "number": "float | int",
        "boolean": "bool",
        "null": "None",
        "unknown": "Any",
        None: "Any",
    }.get(t, "Any")


def is_ref_object(s: Schema) -> bool:
    if s.get("type") != "object":
        return False
    props = s.get("properties", {})
    if not props:
        return False
    ref_keys = {"index", "name", "url"}
    return set(props.keys()).issubset(ref_keys)


def is_ref_like(s: Schema) -> bool:
    # True if schema is a ref-shape or anyOf contains a ref-shape
    if s.get("anyOf"):
        return any(is_ref_object(v) for v in s["anyOf"])
    return is_ref_object(s)


def pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_"))


def to_pydantic_models(root_name: str, schema: Schema, sample_count: int) -> list[str]:
    lines: list[str] = []
    lines.append("from __future__ import annotations")
    lines.append("from typing import Any, Optional, Union, Generic, TypeVar, List, Dict")
    lines.append("from pydantic import BaseModel")
    lines.append("T = TypeVar('T')")
    lines.append("")
    lines.append("class ApiRef(Generic[T], BaseModel):")
    lines.append("    index: str")
    lines.append("    name: str")
    lines.append("    url: str")
    lines.append("")

    nested_models: dict[str, Schema] = {}

    def is_numeric_map(s: Schema) -> tuple[bool, Schema | None]:
        if s.get("type") != "object":
            return (False, None)
        props = s.get("properties", {})
        if not props:
            return (False, None)
        keys = list(props.keys())
        if not keys or not all(k.isdigit() for k in keys):
            return (False, None)
        sig0 = json.dumps(signature_of(next(iter(props.values()))), sort_keys=True)
        for v in props.values():
            if json.dumps(signature_of(v), sort_keys=True) != sig0:
                return (False, None)
        return (True, next(iter(props.values())))

    def collect(prefix: str, s: Schema):
        if s.get("anyOf"):
            for v in s["anyOf"]:
                collect(prefix, v)
            return
        t = s.get("type")
        if t == "object":
            props = s.get("properties", {})
            if props:
                # Skip numeric maps (render as dict[int, T] in fields, no class)
                is_map, _ = is_numeric_map(s)
                # Skip plain reference shapes (render as ApiRef[Any])
                if not is_map and not is_ref_like(s):
                    nested_models.setdefault(prefix, s)
                for k, v in props.items():
                    collect(f"{prefix}_{k}", v)
        elif t == "array":
            collect(f"{prefix}_item", s.get("items", {"type": "unknown"}))

    collect(root_name, schema)

    def pyd_field_type(prefix: str, s: Schema) -> str:
        if is_ref_like(s):
            return "ApiRef[Any]"
        if s.get("anyOf"):
            return " | ".join(pyd_field_type(prefix, x) for x in s["anyOf"])
        t = s.get("type")
        if t == "object":
            if s.get("properties"):
                is_map, v_schema = is_numeric_map(s)
                if is_map and v_schema is not None:
                    return f"dict[int, {pyd_field_type(prefix + '_value', v_schema)}]"
                # Reference by name only; render separately to avoid interleaving
                cls = pascal(prefix)
                return f"'{cls}'"
            return "dict[str, Any]"
        if t == "array":
            return f"list[{pyd_field_type(prefix + '_item', s.get('items', {'type': 'unknown'}))}]"
        return pyd_primitive(t)

    def render_model(name: str, s: Schema):
        props = s.get("properties", {})
        req_counts = s.get("required_counts", {})
        lines.append(f"class {pascal(name)}(BaseModel):")
        if not props:
            lines.append("    # free-form object")
            lines.append("    __root__: Dict[str, Any]")
            lines.append("")
            return
        for k in sorted(props.keys()):
            fs = props[k]
            optional = req_counts.get(k, 0) < sample_count
            typ = "ApiRef[Any]" if is_ref_like(fs) else pyd_field_type(f"{name}_{k}", fs)
            if optional:
                lines.append(f"    {k}: Optional[{typ}] = None")
            else:
                lines.append(f"    {k}: {typ}")
        lines.append("")

    # Render helper models first (exclude root), sorted by depth then name
    helpers = [n for n in nested_models if n != root_name]
    for model_name in sorted(helpers, key=lambda n: (n.count("_"), n)):
        render_model(model_name, nested_models[model_name])

    # Render root model last for readability
    if root_name in nested_models:
        render_model(root_name, nested_models[root_name])

    return lines


# --- Generation ------------------------------------------------------------


def file_slug(path: Path) -> tuple[str, str]:
    # Examples: 5e-SRD-Spells.json -> ("2014", "spells")
    year = path.parts[-2]
    base = path.stem
    name_part = base.replace("5e-SRD-", "").lower()
    return year, name_part


def generate_markdown(path: Path, out_dir: Path, max_items: int = 5) -> Path | None:
    try:
        samples = iter_array_items(path, max_items=max_items)
    except Exception as e:
        print(f"Skipping {path} due to parse error: {e}")
        return None
    if not samples:
        return None

    # Infer schema from samples
    schema: Schema | None = None
    for obj in samples:
        s = schema_of(obj)
        schema = merge_schema(schema, s)

    year, name = file_slug(path)
    title = f"SRD {name.title()} ({year}) — Data Model"

    lines: list[str] = []
    lines.append(f"**{title}**")
    lines.append("")
    lines.append(f"- Source: `{path}`")
    lines.append(f"- Sampled: {len(samples)} entries (not full file)")
    lines.append("- Top-level: array of objects")
    lines.append("")
    lines.append("**Pydantic Models**")
    lines.append("")
    mdl_name = name.rstrip("s") if name.endswith("s") else name
    mdl_lines = to_pydantic_models(mdl_name, schema or {"type": "unknown"}, len(samples))
    lines.append("```python")
    lines.extend(mdl_lines)
    lines.append("```")
    lines.append("")
    lines.append("Notes")
    lines.append("- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.")
    lines.append("- Shapes are inferred from a sample and may omit rare variants.")

    year_prefix = year
    out_path = out_dir / f"{year_prefix}-{name}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    base = Path("docs/5e-database-snippets/src/2014")
    out = Path("docs/data-models")
    out.mkdir(parents=True, exist_ok=True)
    for p in sorted(base.glob("*.json")):
        result = generate_markdown(p, out, max_items=100)
        if result:
            print(f"Wrote {result}")


if __name__ == "__main__":
    main()
