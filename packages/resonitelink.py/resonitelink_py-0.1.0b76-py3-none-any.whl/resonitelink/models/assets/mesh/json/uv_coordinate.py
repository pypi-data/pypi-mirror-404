from abc import ABC

from resonitelink.models.datamodel import Float2, Float3, Float4
from resonitelink.json import MISSING, abstract_json_model, json_model, json_element


__all__ = (
    'UV_Coordinate',
    'UV2D_Coordinate',
    'UV3D_Coordinate',
    'UV4D_Coordinate'
)


@abstract_json_model()
class UV_Coordinate(ABC):
    pass


@json_model("2D", UV_Coordinate)
class UV2D_Coordinate(UV_Coordinate):
    uv : Float2 = json_element("uv", Float2, default=MISSING)


@json_model("3D", UV_Coordinate)
class UV3D_Coordinate(UV_Coordinate):
    uv : Float3 = json_element("uv", Float3, default=MISSING)


@json_model("4D", UV_Coordinate)
class UV4D_Coordinate(UV_Coordinate):
    uv : Float4 = json_element("uv", Float4, default=MISSING)
