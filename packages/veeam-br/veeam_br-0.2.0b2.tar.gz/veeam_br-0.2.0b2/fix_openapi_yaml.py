#!/usr/bin/env python3
"""
Fix OpenAPI YAML/JSON file for 'Cannot take allOf a non-object' errors.

Usage:
  python fix_openapi_yaml.py <input.yaml|json> <output.yaml|json>

This script loads a single OpenAPI file (YAML or JSON), finds schemas that are
referenced from `allOf` and removes `oneOf` and `discriminator` from those
referenced parent schemas when present. The modified content is written to the
specified output file and the input file is not modified.
"""

import sys
import json
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None


def load_file(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("PyYAML is required to read YAML files")
        return yaml.safe_load(text)
    else:
        return json.loads(text)


def dump_file(data, path: Path):
    if path.suffix.lower() in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("PyYAML is required to write YAML files")
        # preserve mapping order
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def find_schemas_used_in_allof(schemas):
    schemas_in_allof = set()
    for name, schema in (schemas or {}).items():
        if isinstance(schema, dict) and "allOf" in schema:
            for item in schema["allOf"]:
                if isinstance(item, dict) and "$ref" in item:
                    ref = item["$ref"]
                    if ref.startswith("#/components/schemas/"):
                        schemas_in_allof.add(ref.split("/")[-1])
    return schemas_in_allof


def fix(data):
    if not isinstance(data, dict):
        raise RuntimeError("OpenAPI root must be an object")

    components = data.get("components", {})
    schemas = components.get("schemas", {})
    used = find_schemas_used_in_allof(schemas)

    fixed = []
    for name in used:
        s = schemas.get(name)
        if not isinstance(s, dict):
            continue
        removed = False
        if "oneOf" in s:
            del s["oneOf"]
            removed = True
        if "discriminator" in s:
            del s["discriminator"]
            removed = True
        if removed:
            fixed.append(name)

    return data, fixed


def main():
    if len(sys.argv) != 3:
        print("Usage: python fix_openapi_yaml.py <input> <output>")
        sys.exit(2)

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not inp.exists():
        print(f"Error: {inp} does not exist")
        sys.exit(1)

    data = load_file(inp)
    new_data, fixed = fix(data)
    dump_file(new_data, out)

    print(f"Wrote {out} — fixed {len(fixed)} schema(s)")
    for n in fixed:
        print(" -", n)


if __name__ == "__main__":
    main()
