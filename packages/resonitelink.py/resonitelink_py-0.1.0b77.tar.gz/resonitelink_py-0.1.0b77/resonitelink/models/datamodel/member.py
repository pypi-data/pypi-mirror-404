from abc import ABC

from resonitelink.json import MISSING, abstract_json_model, json_element


__all__ = (
    'Member',
)

@abstract_json_model()
class Member(ABC):
    id : str = json_element("id", str, init=False, default=MISSING)
