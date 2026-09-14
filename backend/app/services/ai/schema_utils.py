from pydantic import BaseModel


def _convert_schema(node: dict, defs: dict) -> dict:
    if "$ref" in node:
        ref_name = node["$ref"].split("/")[-1]
        node = defs[ref_name]

    if "anyOf" in node:
        variants = [v for v in node["anyOf"] if v.get("type") != "null"]
        is_nullable = any(v.get("type") == "null" for v in node["anyOf"])
        result = _convert_schema(variants[0], defs) if variants else {}
        if is_nullable:
            result["nullable"] = True
        if "description" in node:
            result["description"] = node["description"]
        return result

    result = {}
    for key, value in node.items():
        if key in ("$defs", "title", "default"):
            continue
        elif key == "properties":
            # Recurse into each field's schema individually — this dict's
            # keys are field NAMES (e.g. "title", "sections"), not schema
            # metadata, so they must never be stripped here even if a key
            # happens to collide with a metadata key name like "title".
            result["properties"] = {
                name: _convert_schema(sub, defs) for name, sub in value.items()
            }
        elif key == "items":
            result["items"] = _convert_schema(value, defs)
        elif isinstance(value, dict):
            result[key] = _convert_schema(value, defs)
        elif isinstance(value, list):
            result[key] = [_convert_schema(v, defs) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result


def pydantic_to_gemini_schema(model: type[BaseModel]) -> dict:
    """Gemini's response_schema doesn't support $ref/$defs (used for nested
    Pydantic models) or anyOf-based optionality — it wants everything
    inlined, with 'nullable: true' instead. This flattens a Pydantic
    model's JSON Schema into that shape."""
    raw = model.model_json_schema()
    defs = raw.get("$defs", {})
    return _convert_schema(raw, defs)
