from resonitelink.json import MISSING, json_model, json_element

from resonitelink.models.datamodel import Member, Field


__all__ = (
    'Field_Enum',
    'Field_Nullable_Enum',
)


@json_model("enum", Member)
class Field_Enum(Field):
    value : str = json_element("value", str, default=MISSING)
    enum_type : str = json_element("enumType", str, default=MISSING)

    @property
    def value_type_name(self) -> str:
        return "enum"


@json_model("enum?", Member)
class Field_Nullable_Enum(Field):
    value : str = json_element("value", str, default=MISSING)
    enum_type : str = json_element("enumType", str, default=MISSING)

    @property
    def value_type_name(self) -> str:
        return "enum?"
