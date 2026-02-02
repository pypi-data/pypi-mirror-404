from resonitelink.models.datamodel import Component
from resonitelink.models.messages import Message
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'GetComponent',
    'AddComponent',
    'UpdateComponent',
    'RemoveComponent',
)


@json_model("getComponent", Message)
class GetComponent(Message):
    component_id : str = json_element("componentId", str, default=MISSING)


@json_model("addComponent", Message)
class AddComponent(Message):
    data : Component = json_element("data", Component, default=MISSING)
    container_slot_id : str = json_element("containerSlotId", str, default=MISSING)


@json_model("updateComponent", Message)
class UpdateComponent(Message):
    data : Component = json_element("data", Component, default=MISSING)


@json_model("removeComponent", Message)
class RemoveComponent(Message):
    component_id : str = json_element("componentId", str, default=MISSING)
