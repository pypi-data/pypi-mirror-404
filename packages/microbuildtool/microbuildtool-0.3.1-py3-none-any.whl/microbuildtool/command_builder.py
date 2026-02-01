from typing import Any
from string import Template


def build_cmd(command_template: list[str], namespace: dict[str, Any]) -> list[str]:
    namespace = {key.upper(): val for key, val in namespace.items()}
    return [
        Template(part).substitute(namespace)
        for part in command_template
    ]
