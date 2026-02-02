#       >=============================================================================<
# NOTE: !!! THIS FILE IS AUTO-GENERATED! DO NOT EDIT! MODIFY CODEGENERATOR INSTEAD! !!!
#       >=============================================================================<
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'FloatQ',
    'DoubleQ',
)


@json_model(internal_type_name="t_floatQ")
class FloatQ():
    x : float = json_element("x", float, default=MISSING)
    y : float = json_element("y", float, default=MISSING)
    z : float = json_element("z", float, default=MISSING)
    w : float = json_element("w", float, default=MISSING)


@json_model(internal_type_name="t_doubleQ")
class DoubleQ():
    x : float = json_element("x", float, default=MISSING)
    y : float = json_element("y", float, default=MISSING)
    z : float = json_element("z", float, default=MISSING)
    w : float = json_element("w", float, default=MISSING)
