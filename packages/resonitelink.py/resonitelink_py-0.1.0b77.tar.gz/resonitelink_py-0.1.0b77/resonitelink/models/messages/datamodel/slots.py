from resonitelink.models.datamodel import Slot
from resonitelink.models.messages import Message
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'GetSlot',
    'AddSlot',
    'UpdateSlot',
    'RemoveSlot',
)


@json_model("getSlot", Message)
class GetSlot(Message):
    slot_id : str = json_element("slotId", str, default=MISSING)
    depth : int = json_element("depth", int, default=MISSING)
    include_component_data : bool = json_element("includeComponentData", bool, default=MISSING)


@json_model("addSlot", Message)
class AddSlot(Message):
    data : Slot = json_element("data", Slot, default=MISSING)


@json_model("updateSlot", Message)
class UpdateSlot(Message):
    data : Slot = json_element("data", Slot, default=MISSING)


@json_model("removeSlot", Message)
class RemoveSlot(Message):
    slot_id : str = json_element("slotId", str, default=MISSING)
