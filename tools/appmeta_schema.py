appmeta_schema = \
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "version" : {"type" : "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
        "type": {
            "anyOf": [
                {"enum": ["watchface", "face","app","application"]},
                {"type":"integer"}
            ]
        },
        "display_name": {"type": "string"},
        "theme_class": {"type": "string"}
    },
    "required": [ "version", "type", "display_name"]
}