import string

def render_template_path(template: str, values: dict | None = None) -> str:
    formatter = string.Formatter()

    required_fields = [field for _, field, _, _ in formatter.parse(template) if field]

    if not required_fields:
        return template

    if not values:
        raise ValueError(f"Values are expected but not set")

    missing = [field for field in required_fields if field not in values]

    if missing:
        raise ValueError(f"Variables not set: {', '.join(missing)}")

    return template.format(**values)