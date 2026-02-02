from resonitelink.models.messages import Message
from resonitelink.json import json_model


__all__ = (
    'RequestSessionData',
)


@json_model("requestSessionData", Message)
class RequestSessionData(Message):
    pass