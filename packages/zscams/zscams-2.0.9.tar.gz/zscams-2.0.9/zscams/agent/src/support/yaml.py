import yaml


class YamlIndentedListsDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YamlIndentedListsDumper, self).increase_indent(flow, False)

def resolve_placeholders( obj, values: dict[str, int]):
    """
    Recursively replace '{key}' strings with values[key]
    in dicts, lists, and strings.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = resolve_placeholders(v, values)

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = resolve_placeholders(v, values)

    elif isinstance(obj, str):
        for key, value in values.items():
            placeholder = f"{{{key}}}"
            if obj == placeholder:
                return value
        return obj

    return obj
def assert_no_placeholders_left(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            assert_no_placeholders_left(v)
    elif isinstance(obj, list):
        for v in obj:
            assert_no_placeholders_left(v)
    elif isinstance(obj, str) and obj.startswith("{") and obj.endswith("}"):
        raise ValueError(f"Unresolved placeholder: {obj}")