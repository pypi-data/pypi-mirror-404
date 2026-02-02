from resonitelink.json import json_model

from resonitelink.models.datamodel import Member


__all__ = (
    'EmptyElement',
)


@json_model("empty", Member)
class EmptyElement(Member):
    pass
