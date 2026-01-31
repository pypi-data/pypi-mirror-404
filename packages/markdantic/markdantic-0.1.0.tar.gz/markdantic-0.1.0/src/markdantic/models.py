from dataclasses import dataclass


@dataclass
class FieldDoc:
    name: str
    type: str
    required: bool
    default: str
    description: str


@dataclass
class ModelDoc:
    name: str
    base: str
    doc: str
    fields: list[FieldDoc]
