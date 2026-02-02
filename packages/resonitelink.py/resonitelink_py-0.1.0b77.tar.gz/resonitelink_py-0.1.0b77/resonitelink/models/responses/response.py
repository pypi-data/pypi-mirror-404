from abc import ABC

from resonitelink.json import MISSING, abstract_json_model, json_model, json_element


__all__ = (
    'Response',
    'GenericResponse',
)


@abstract_json_model()
class Response(ABC):
    source_message_id : str = json_element("sourceMessageId", str, default=MISSING)
    success : bool = json_element("success", bool, default=MISSING)
    error_info : str = json_element("errorInfo", str, default=MISSING)


@json_model(type_name="response", derived_from=Response)
class GenericResponse(Response):
    pass
