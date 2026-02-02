from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'Color',
    'Color32',
    'ColorX'
)


@json_model(internal_type_name="t_color")
class Color():
    r : float = json_element("r", float, default=MISSING)
    g : float = json_element("g", float, default=MISSING)
    b : float = json_element("b", float, default=MISSING)
    a : float = json_element("a", float, default=MISSING)


@json_model(internal_type_name="t_color32")
class Color32():
    r : int = json_element("r", int, default=MISSING)
    g : int = json_element("g", int, default=MISSING)
    b : int = json_element("b", int, default=MISSING)
    a : int = json_element("a", int, default=MISSING)


@json_model(internal_type_name="t_colorX")
class ColorX():
    r : float = json_element("r", float, default=MISSING)
    g : float = json_element("g", float, default=MISSING)
    b : float = json_element("b", float, default=MISSING)
    a : float = json_element("a", float, default=MISSING)
    profile : str = json_element("profile", str, default=MISSING)
