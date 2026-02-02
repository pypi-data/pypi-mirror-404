from abc import ABC

from resonitelink.json import MISSING, abstract_json_model, json_element


__all__ = (
    'Worker',
)


@abstract_json_model()
class Worker(ABC):
    id : str = json_element("id", str, default=MISSING)
    is_reference_only : bool = json_element("isReferenceOnly", bool, default=MISSING)
