"""Base model of the check contracts and how their docstrings reach the JSON Schema.

Features:
    ADR-02
"""

import re

from pydantic import BaseModel, ConfigDict
from pydantic.json_schema import JsonDict


def _schema_description(schema: JsonDict) -> None:
    # Attributes and Features document the code; the published schema keeps the prose.
    description = schema.get("description")
    if isinstance(description, str):
        schema["description"] = re.split(
            r"\n\n(?:Attributes|Features):\n", description, maxsplit=1
        )[0]


class _Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, json_schema_extra=_schema_description
    )
