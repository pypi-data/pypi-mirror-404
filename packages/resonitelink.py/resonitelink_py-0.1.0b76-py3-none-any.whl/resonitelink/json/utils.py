from .models import MISSING, JSONModel, _JSONPropertyType
from typing import Any, List, Callable


__all__ = (
    'optional',
    'format_object_structure',
)


def optional(value : Any, func : Callable[[], Any]) -> Any:
    """
    If value is MISSING, returns MISSING.
    Otherwise returns result of func.

    """
    if value is MISSING:
        return MISSING
    else:
        return func()


def format_object_structure(obj : Any, print_missing : bool = False, prefix : str = "") -> str:
    """
    Produces a string for the given object that represents that object's structure.
    If that object is an instance of a registered model's data class, it will be resolved recursively.
    This is mainly intended for debugging purposes.

    Parameters
    ----------
    obj : Any
        The object to analyze.
    print_missing : bool
        Wether to list missing property members when resolving model structure.
    prefix : str
        String to prefix before message. Each recursion level pads this with leading spaces.
    
    Returns
    -------
    A string representing the object's structure.

    """
    structure_str : str
    try:
        # Attempt to find model for potential model's data class
        model = JSONModel.find_model(target_type=type(obj))
    
    except KeyError:
        # Not a model
        structure_str = f"Type '{type(obj).__name__}': {obj}"
    
    else:
        # Model class, resolve children
        property_lines : List[str] = []
        for key, json_property in model.properties.items():
            if hasattr(obj, key):
                # Value for key present
                val = getattr(obj, key)

                if json_property.property_type == _JSONPropertyType.LIST and isinstance(val, list):
                    # Resolve property as list
                    if len(val) == 0:
                        # Empty list
                        property_lines.append(f" - {key} (List): []")
                    else:
                        property_lines.append(f" - {key} (List):\n{prefix}    - {f'\n{prefix}    - '.join([ format_object_structure(v, prefix=f'{prefix}      ') for v in val ])}")

                elif json_property.property_type == _JSONPropertyType.DICT and isinstance(val, dict):
                    # Resolve property as dict
                    if len(val.items()) == 0:
                        # Empty dict
                        property_lines.append(f" - {key} (Dict): {{}}")
                    else:
                        property_lines.append(f" - {key} (Dict):\n{prefix}    - {f'\n{prefix}    - '.join([ f'{k}: {format_object_structure(v, prefix=f'{prefix}      ')}' for k, v in val.items() ])}")
                
                else:
                    # Resolve property as single element
                    property_lines.append(f" - {key}: {format_object_structure(val, prefix=f"{prefix}   ")}")
            
            elif print_missing:
                # Value for key missing & missing values should be printed
                property_lines.append(f"{key}: MISSING")
        
        structure_str = f"Type '{type(obj).__name__}':\n{prefix}{f'\n{prefix}'.join(property_lines)}"

    return structure_str
