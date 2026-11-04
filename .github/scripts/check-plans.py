"""Checks for the plans and data files of AppThreat/.github.

Run from the repository root: python3 -I .github/scripts/check-plans.py

1. Every JSON file parses.
2. Every plans/*.corpus.json validates against plans/corpus-manifest.schema.json, and its item
   names are unique.
3. Markdown files have no em-dashes and no emojis (the writing rules of these repositories), and
   their relative links point at files that exist.

The script uses the standard library only. The schema validator below implements the keywords the
corpus schema uses and fails on any other keyword, so a schema change cannot pass unchecked.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(".")
SKIP_DIRS = {".git", "node_modules"}
KNOWN_KEYWORDS = {
    "$id",
    "$schema",
    "title",
    "description",
    "type",
    "required",
    "additionalProperties",
    "properties",
    "items",
    "pattern",
    "enum",
    "minimum",
}
TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def files(pattern):
    return sorted(p for p in ROOT.rglob(pattern) if not SKIP_DIRS & set(p.parts))


def type_ok(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def validate(value, schema, where, errors):
    unknown = set(schema) - KNOWN_KEYWORDS
    if unknown:
        errors.append(f"{where}: the schema uses keywords this check does not know: {sorted(unknown)}")
        return
    if "type" in schema and not type_ok(value, schema["type"]):
        errors.append(f"{where}: expected {schema['type']}")
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        errors.append(f"{where}: {value!r} does not match {schema['pattern']}")
    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        errors.append(f"{where}: {value} is below {schema['minimum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing {key!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], f"{where}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{where}: {key!r} is not allowed")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{where}[{i}]", errors)


def main():
    errors = []
    documents = {}
    for path in files("*.json"):
        try:
            documents[path] = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"{path}: not valid JSON: {e}")

    schema = documents.get(Path("plans/corpus-manifest.schema.json"))
    manifests = [p for p in documents if p.parent == Path("plans") and p.name.endswith(".corpus.json")]
    if schema is None:
        errors.append("plans/corpus-manifest.schema.json is missing or not valid JSON")
    else:
        for path in manifests:
            validate(documents[path], schema, str(path), errors)
            names = [item.get("name") for item in documents[path].get("items", []) if isinstance(item, dict)]
            for name in sorted({n for n in names if names.count(n) > 1}):
                errors.append(f"{path}: item name {name!r} is used more than once")

    for path in files("*.md"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "—" in line:
                errors.append(f"{path}:{number}: em-dash")
            if EMOJI.search(line):
                errors.append(f"{path}:{number}: emoji")
            for target in LINK.findall(line):
                if "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).exists():
                    errors.append(f"{path}:{number}: link to {target}, which does not exist")

    for error in errors:
        print(error)
    print(f"{len(documents)} JSON files, {len(manifests)} corpus manifests, {len(files('*.md'))} Markdown files: "
          f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
