from abc import ABC

from resonitelink.json import abstract_json_model


__all__ = (
    'Submesh',
)


@abstract_json_model()
class Submesh(ABC):
    pass
