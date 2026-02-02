from abc import ABC, abstractmethod

from resonitelink.json import MISSING, abstract_json_model, json_element


__all__ = (
    'Message',
    'BinaryPayloadMessage',
)


@abstract_json_model()
class Message(ABC):
    message_id : str = json_element("messageId", str, default=MISSING, init=False)


@abstract_json_model()
class BinaryPayloadMessage(Message, ABC):
    @property
    @abstractmethod
    def raw_binary_payload(self) -> bytes:
        raise NotImplementedError()

    @raw_binary_payload.setter
    @abstractmethod
    def raw_binary_payload(self, data : bytes):
        raise NotImplementedError()
