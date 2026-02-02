from __future__ import annotations # Delayed evaluation of type hints (PEP 563)

from typing import List

from resonitelink.models.datamodel.primitives_containers import Field_Float3, Field_FloatQ, Field_Bool, Field_String, Field_Long
from resonitelink.models.datamodel.members import Reference
from resonitelink.models.datamodel.workers import Component
from resonitelink.models.datamodel import Worker
from resonitelink.json import MISSING, SELF, json_model, json_element, json_list


__all__ = (
    'Slot',
)


@json_model() # NOT derived from Worker, it's the same in the reference C# implementation.
class Slot(Worker):
    parent : Reference = json_element("parent", Reference, default=MISSING)
    position : Field_Float3 = json_element("position", Field_Float3, default=MISSING)
    rotation : Field_FloatQ = json_element("rotation", Field_FloatQ, default=MISSING)
    scale : Field_Float3 = json_element("scale", Field_Float3, default=MISSING)
    is_active : Field_Bool = json_element("isActive", Field_Bool, default=MISSING)
    is_persistent : Field_Bool = json_element("isPersistent", Field_Bool, default=MISSING)
    name : Field_String = json_element("name", Field_String, default=MISSING)
    tag : Field_String = json_element("tag", Field_String, default=MISSING)
    order_offset : Field_Long = json_element("orderOffset", Field_Long, default=MISSING)

    components : List[Component] = json_list("components", Component, default=MISSING)
    children : List[Slot] = json_list("children", SELF, default=MISSING)

    # Special Slot references
    Root = Reference(target_id="Root", target_type="[FrooxEngine]FrooxEngine.Slot")
