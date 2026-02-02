#       >=============================================================================<
# NOTE: !!! THIS FILE IS AUTO-GENERATED! DO NOT EDIT! MODIFY CODEGENERATOR INSTEAD! !!!
#       >=============================================================================<
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'Float2x2',
    'Float3x3',
    'Float4x4',
    'Double2x2',
    'Double3x3',
    'Double4x4',
)


@json_model(internal_type_name="t_float2x2")
class Float2x2():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)


@json_model(internal_type_name="t_float3x3")
class Float3x3():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m02 : float = json_element("m02", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)
    m12 : float = json_element("m12", float, default=MISSING)
    m20 : float = json_element("m20", float, default=MISSING)
    m21 : float = json_element("m21", float, default=MISSING)
    m22 : float = json_element("m22", float, default=MISSING)


@json_model(internal_type_name="t_float4x4")
class Float4x4():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m02 : float = json_element("m02", float, default=MISSING)
    m03 : float = json_element("m03", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)
    m12 : float = json_element("m12", float, default=MISSING)
    m13 : float = json_element("m13", float, default=MISSING)
    m20 : float = json_element("m20", float, default=MISSING)
    m21 : float = json_element("m21", float, default=MISSING)
    m22 : float = json_element("m22", float, default=MISSING)
    m23 : float = json_element("m23", float, default=MISSING)
    m30 : float = json_element("m30", float, default=MISSING)
    m31 : float = json_element("m31", float, default=MISSING)
    m32 : float = json_element("m32", float, default=MISSING)
    m33 : float = json_element("m33", float, default=MISSING)


@json_model(internal_type_name="t_double2x2")
class Double2x2():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)


@json_model(internal_type_name="t_double3x3")
class Double3x3():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m02 : float = json_element("m02", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)
    m12 : float = json_element("m12", float, default=MISSING)
    m20 : float = json_element("m20", float, default=MISSING)
    m21 : float = json_element("m21", float, default=MISSING)
    m22 : float = json_element("m22", float, default=MISSING)


@json_model(internal_type_name="t_double4x4")
class Double4x4():
    m00 : float = json_element("m00", float, default=MISSING)
    m01 : float = json_element("m01", float, default=MISSING)
    m02 : float = json_element("m02", float, default=MISSING)
    m03 : float = json_element("m03", float, default=MISSING)
    m10 : float = json_element("m10", float, default=MISSING)
    m11 : float = json_element("m11", float, default=MISSING)
    m12 : float = json_element("m12", float, default=MISSING)
    m13 : float = json_element("m13", float, default=MISSING)
    m20 : float = json_element("m20", float, default=MISSING)
    m21 : float = json_element("m21", float, default=MISSING)
    m22 : float = json_element("m22", float, default=MISSING)
    m23 : float = json_element("m23", float, default=MISSING)
    m30 : float = json_element("m30", float, default=MISSING)
    m31 : float = json_element("m31", float, default=MISSING)
    m32 : float = json_element("m32", float, default=MISSING)
    m33 : float = json_element("m33", float, default=MISSING)
