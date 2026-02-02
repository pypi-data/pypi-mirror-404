from __future__ import annotations # Delayed evaluation of type hints (PEP 563)

from dataclasses import dataclass, field, fields
from typing import Optional, Any, Type, Tuple, List, Dict, Generator, TypeVar, Generic, dataclass_transform
from enum import Enum
import logging


__all__ = (
    'MISSING',
    'SELF',
    'JSONProperty',
    'JSONModel',
    'json_element',
    'json_list',
    'json_dict',
    'json_model',
    'abstract_json_model'
)


logger = logging.getLogger("ResoniteLinkModels")
logger.setLevel(logging.DEBUG)


class _Sentinel:
    """
    Base class for sentinel values used in this library.

    """
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'

# Sentinel used to represent missing values.
# NOTE: Missing values are NOT `null`, they are *missing* (i.e. they won't be included in JSON objects)!
MISSING: Any = _Sentinel()

# Sentinel used to represent self references.
# This can be used when a JSONProperty of a JSONModel is of the containing model's type (recursion).
SELF : Any = _Sentinel()


class _JSONPropertyType(Enum):
    ELEMENT = 0,
    LIST = 1,
    DICT = 2


class JSONProperty():
    """
    Denotes a JSON property of a model data class that will be picked up by the serializer / deserializer.

    Usually this isn't instantiated directly, instead, `json_element`, `json_list` or `json_dict` are used to denote a field as a JSONProperty. 
    
    Example
    -------
        @json_model(type_name="example")
        def ExampleModel():
            example_element : int = json_element("exampleElement", int, default=MISSING)
            example_list : List[int] = json_list("exampleList", int, default=MISSING)
            example_dict : Dict[str, int] = json_dict("exampleDict", int, default=MISSING)
    
    """
    _json_name : str
    _element_type : type
    _property_type : _JSONPropertyType
    _abstract : bool

    @property
    def json_name(self) -> str:
        return self._json_name

    @property
    def element_type(self) -> type:
        return self._element_type
    
    @property
    def property_type(self) -> _JSONPropertyType:
        return self._property_type
    
    @property
    def abstract(self) -> bool:
        return self._abstract

    def __init__(self, json_name : str, element_type : type, property_type : _JSONPropertyType, abstract : bool):
        """
        Defines a new JSONProperty.

        Parameters
        ----------
        json_name : str
            The name of this property in the containing JSON object.
        element_type : type
            The type of the target element of this property.
            NOTE: For lists, this is the type of the element in the list. For dicts, this is the value of the dict (dict key is always of type `str`).
        property_type : _JSONPropertyType
            The type of this property (Element, List, or Dict).
        abstract : bool
            Whether this property is "abstract" and needs to be overridden by a implementing class. If a `JSONModel` with
            an abstract `JSONProperty` is created, a `TypeError` will be raised.

        """
        self._json_name = json_name
        self._element_type = element_type
        self._property_type = property_type
        self._abstract = abstract
    
    def __repr__(self) -> str:
        return f"<JSONProperty name='{self.json_name}', element_type={self.element_type}, property_type={self.property_type}{' (abstract)' if self._abstract else ''}>"


def _json_property(json_name : str, element_type : type, *, default : Any, init = True, property_type : _JSONPropertyType = _JSONPropertyType.ELEMENT, abstract = False):
    """
    Utility function for easily defining fields in a dataclass as JSON-Properties.
    Returns a field for use in dataclass.

    Notes
    -----
    - The function signature is REQUIRED to be compatible with `dateclasses.type()`, as type checkers assume so. 
      - Because of this, the `default` argument HAS to be kw-only, and it CANNOT have a default value.
      - Because of this, the `init` argument HAS to default to `True`
    - This doesn't provide proper static type hinting, as it returns 'Any'.
    - For static type hinting, use json_element, json_list or json_dict respectively.

    """
    json_prop = JSONProperty(json_name=json_name, element_type=element_type, property_type=property_type, abstract=abstract)

    return field(default=default, init=init, metadata={'JSONProperty': json_prop})


def json_element[T](json_name : str, element_type : Type[T], *, default : Any, init = True, abstract = False) -> T:
    """
    Utility function for easily definiing fields in dataclasses as JSON-Element-Properties.
    Returns a field for use in dataclass.

    Notes
    -----
    - The function signature is REQUIRED to be compatible with `dateclasses.type()`, as type checkers assume so. 
      - Because of this, the `default` argument HAS to be kw-only, and it CANNOT have a default value.
      - Because of this, the `init` argument HAS to default to `True`

    """
    return _json_property(json_name=json_name, element_type=element_type, default=default, init=init, property_type=_JSONPropertyType.ELEMENT, abstract=abstract)


def json_list[T](json_name : str, element_type : Type[T], *, default : Any, init = True, abstract = False) -> List[T]:
    """
    Utility function for easily definiing fields in dataclasses as JSON-List-Properties.
    Returns a field for use in dataclass.

    Notes
    -----
    - The function signature is REQUIRED to be compatible with `dateclasses.type()`, as type checkers assume so. 
      - Because of this, the `default` argument HAS to be kw-only, and it CANNOT have a default value.
      - Because of this, the `init` argument HAS to default to `True`

    """
    return _json_property(json_name=json_name, element_type=element_type, default=default, init=init, property_type=_JSONPropertyType.LIST, abstract=abstract)


def json_dict[T](json_name : str, element_type : Type[T], *, default : Any, init = True, abstract = False) -> Dict[str, T]:
    """
    Utility function for easily definiing fields in dataclasses as JSON-Dict-Properties.
    Returns a field for use in dataclass.

    Notes
    -----
    - The function signature is REQUIRED to be compatible with `dateclasses.type()`, as type checkers assume so. 
      - Because of this, the `default` argument HAS to be kw-only, and it CANNOT have a default value.
      - Because of this, the `init` argument HAS to default to `True`

    """
    return _json_property(json_name=json_name, element_type=element_type, default=default, init=init, property_type=_JSONPropertyType.DICT, abstract=abstract)


D = TypeVar('D', bound=Type)
class JSONModel(Generic[D]):
    """
    Denotes a JSON serializable model class that can have JSON serializable properties.
    Models are associated with data classes, which hold the actual data when deserialized.
    JSON models support polymorphism, where multiple instances of the same base class are identified via a '$type' parameter in the JSON objects.

    Usually this isn't instantiated directly, instead, `json_model` is used as a decorator on the model's data class. 
    
    """
    _model_data_class_mapping : Dict[Type, JSONModel] = {} # Mapping from data class to model.
    _global_model_type_name_mapping : Dict[str, JSONModel] = {} # Mappings of model type names for all non-derived (global) models.
    _derived_model_type_name_mappings : Dict[Type, Dict[str, JSONModel]] = {} # Mapping from base type to all .
    _internal_model_type_name_mappings : Dict[str, JSONModel] = {} # Mappings for internal type names only.

    _data_class : D
    _type_name : Optional[str]
    _derived_from : Optional[type]
    _internal_type_name : Optional[str] # Can be used as an unique internal identifier for types, but has no impact on JSON serialization / deserialization.
    _properties : Dict[str, JSONProperty]
    _property_name_mapping : Dict[str, str]
    
    @property
    def data_class(self) -> D:
        return self._data_class
    
    @property
    def type_name(self) -> Optional[str]:
        return self._type_name
    
    @property
    def derived_from(self) -> Optional[type]:
        return self._derived_from
    
    @property
    def internal_type_name(self) -> Optional[str]:
        return self._internal_type_name
    
    @property
    def properties(self) -> Dict[str, JSONProperty]:
        return self._properties
    
    @property
    def property_name_mapping(self) -> Dict[str, str]:
        return self._property_name_mapping

    def __init__(self, data_class : D, type_name : Optional[str] = None, derived_from : Optional[type] = None, internal_type_name : Optional[str] = None):
        if derived_from is not None and not type_name:
            raise ValueError(f"A `type_name` needs to be speficied if the model is derived!")
        
        self._data_class = data_class
        self._type_name = type_name
        self._derived_from = derived_from
        self._internal_type_name = internal_type_name
        self._properties = dict(self._find_properties_in_data_class(self.data_class))
        self._verify_properties(self._properties)
        self._property_name_mapping = dict(self._get_property_name_mapping(self._properties))
        self._register()
    
    def _find_properties_in_data_class(self, data_class : D) -> Generator[Tuple[str, JSONProperty], Any, Any]:
        """
        Inspects the specified data class and produces key-value pairs for all defined JSONProperties.
        Also recursively processes all base classes (if any).

        Returns
        -------
        Generator object that produces tuples for each each field annoated with JSONProperty, where tpl[0] is the annoated field name,
        and tpl[1] is the first JSONProperty found in its annotation metadata.

        """
        for field in fields(data_class):
            if 'JSONProperty' not in field.metadata:
                # We can skip all fields that don't have 'JSONProperty' metadata.
                continue

            # Get JSONProperty instance from field metadata
            json_prop = field.metadata['JSONProperty']
            if not isinstance(json_prop, JSONProperty):
                raise TypeError(f"Expected 'JSONProperty' field metadata to be of type 'JSONProperty', not '{type(json_prop)}'!")
            
            # Yield field name and associated JSONProperty
            yield (field.name, json_prop)
    
    def _verify_properties(self, properties : Dict[str, JSONProperty]):
        """
        Verifies the provided properties.
        This is needed as a separate step for issues that can only be detected after all properties have been passed,
        for example wether a abstract JSONProperty has not been overridden.

        """
        for key, json_prop in properties.items():
            if json_prop.abstract:
                # Abstract property that wasn't overridden
                raise TypeError(f"Invalid properties for JSONModel '{self}': Data class does not provide concrete implementation of abstract JSONProperty '{json_prop}'!")

    
    def _get_property_name_mapping(self, properties : Dict[str, JSONProperty]) -> Generator[Tuple[str, str], Any, Any]:
        """
        Produces key-value pair mappings for each property to associate every JSONProperty's (unique) name with the
        name of the corresponding annotated field in the model's data class.

        Parameters
        ----------
        properties : Dict[str, JSONProperty]
            Properties to generate JSON name mappings for.

        Returns
        -------
        Generator object that produces tuples for each item in the provided properties dict, where tpl[0] is the JSONProperty's (unique) name,
        and tpl[1] is the name of the corresponding annotated field in the model's data class.

        """
        for key, json_prop in properties.items():
            yield json_prop.json_name, key

    def _register(self):
        """
        Registers this model.
        
        Raises
        ------
        KeyError
            If a model with the same type name is already registered, or if this model instance is already registered under a different name.

        """
        if self.data_class in JSONModel._model_data_class_mapping.keys():
            raise KeyError(f"A different model with data class '{self.data_class}' is already registered!")
        if self in JSONModel._global_model_type_name_mapping.values():
            raise KeyError(f"This model instance is already registered under a different type name!")
        if self.internal_type_name and self.internal_type_name in JSONModel._internal_model_type_name_mappings.keys():
            raise KeyError(f"A different model with internal type name '{self.internal_type_name}' is already registered!")
        
        logger.debug(f"Registering JSONModel '{self.type_name}' with data class '{self.data_class}':")
        if len(self.properties) == 0:
            logger.debug(f"  -> No fields annotated with JSONProperty found!")
            logger.warning(f"Data class '{self.data_class}' of JSONModel '{self.type_name}' has no fields annotated with JSONProperty!")
        else:
            for key, json_prop in self.properties.items():
                logger.debug(f"  -> '{key}': {json_prop}")
        
        JSONModel._model_data_class_mapping[self.data_class] = self # type: ignore
        
        if self.derived_from is not None:
            # Register as derived model
            derived_mappings = JSONModel._derived_model_type_name_mappings.setdefault(self.derived_from, {})
            type_name : str = self.type_name # type: ignore This will never be `None` if derived_from is specified (ensured in constructor).

            if type_name in derived_mappings.keys():
                raise KeyError(f"A different model derived from '{self.derived_from}' with type name '{self.type_name}' is already registered!")
            
            derived_mappings[type_name] = self

        elif self.type_name:
            # Register as global model
            if self.type_name in JSONModel._global_model_type_name_mapping.keys():
                raise KeyError(f"A different global model with type name '{self.type_name}' is already registered!")
            
            JSONModel._global_model_type_name_mapping[self.type_name] = self
        
        if self.internal_type_name:
            JSONModel._internal_model_type_name_mappings[self.internal_type_name] = self
    
    @staticmethod
    def find_model(target_type : Optional[type] = None, target_type_name : Optional[str] = None) -> JSONModel:
        """
        Searches for a registered `JSONModel`. The following search order is used:

        1. A registered model with a data class that matches target_type.
        2. A registered model that is derived from target_type matching the specified target_type_name.
        3. A registered model that is not derived (global) matching the specified target_type_name.

        Notes
        -----
        * If the `target_type` originates from an already object instance, it should never be the base of a derived model, as abstract bases should never get instanced!

        Parameters
        ----------
        target_type : Optional[type]
            Type to select a model for. This is either a model's data class, or a base class of one or more derived models.
            If not provided, only non-derived (global) models can be found based on the specified target_type_name.
        target_type_name : Optional[str]
            The type name to search a model for. This is either a derived model's type name, or a non-derived (global) model's type name.
            If not provided, only models with with a data class that exactly matches the specified target_type can be found.
        
        Returns
        -------
        The found `JSONModel` instance.
        
        Raises
        ------
        ValueError
            When `target_type` is a base class of one or more derived models, but `target_type_name` was not specified.
        KeyError
            When no model was found for the specified `target_type` and / or `target_type_name`.

        """
        if target_type is not None:
            # Type specified
            if target_type in JSONModel._model_data_class_mapping:
                # Target type is registered as a data class of a model, return associated model
                return JSONModel._model_data_class_mapping[target_type]
            
            if target_type in JSONModel._derived_model_type_name_mappings:
                # Target type is base for one or more derived models. In this case we also need a type name.
                if target_type_name is None:
                    raise ValueError(f"Target type '{target_type}' is a base for one or more derived models, but no `target_type_name` was specified to select one!")

                # Will raise a KeyError if no derived model for specified type name is registered.
                return JSONModel._derived_model_type_name_mappings[target_type][target_type_name]
        
        if target_type_name is not None:
            # Assume  if the type name corresponds with a non-derived (global) model.
            return JSONModel._global_model_type_name_mapping[target_type_name]
        
        raise KeyError(f"No model found for `target_type` {target_type} and / or `target_type_name` {target_type_name}`")
    
    @staticmethod
    def find_model_internal(target_internal_type_name : str) -> JSONModel:
        """
        Searches for a registered `JSONModel` by its `internal_type_name`.
        Is only able to find models that specify an `internal_type_name`.
        The `internal_type_name` has to be globally unique. 

        Parameters
        ----------
        target_internal_type_name : str
            The `internal_type_name` of the model to find.
        
        Returns
        -------
        The found `JSONModel` instance.

        Raises
        ------
        KeyError
            When no model was found for the specified `target_internal_type_name`.

        """
        return JSONModel._internal_model_type_name_mappings[target_internal_type_name]
    
    def __repr__(self) -> str:
        return f"<JSONModel data_class={self.data_class}, type_name='{self.type_name}', derived_from={self.derived_from}, internal_type_name='{self.internal_type_name}', property_count={len(self.properties)}>"


# This decorator tells type checkers that the returned object behaves like a dataclass (because it is one),
# but we're also specifying our custon property functions as field specifiers. Otherwise, those would *not* get
# recognized as dataclass field specifiers by type checkers, and those would produce incorrect type information.
@dataclass_transform(field_specifiers=(field, _json_property, json_element, json_list, json_dict))
def json_model[T](type_name : Optional[str] = None, derived_from : Optional[type] = None, internal_type_name : Optional[str] = None, slots=True):
    """
    Class decorator to easily declare models from their data classes.
    The type will be wrapped into a dataclass.

    Parameters
    ----------
    type_name : str
        The model type name to associate the decorated data class with.
        (This will be used by JSON serializer / deserializer as the '$type' value.)
    derive_from : type, optional
        Used to represent polymorphic relationship to a base model.
        The data class should also inherit the specified base model's data class.
    internal_type_name : str, optional
        Globally unique internal type name. This has no impact on JSON serialization / deserializing.
        This can be used if you need to find models by name in your code, but need the identifier to be separate from the actual
        JSON type name.
    slots : bool, default = True
        Argument passed through to dataclass constructor.
        Controls wether the dataclass should use `__slots__` for fields.

    """
    def _wrapper(cls : Type[T]) -> Type[T]:
        # Wrap the decorated class wrapped into a dataclass
        data_class = dataclass(cls, slots=slots)
        
        # Creating a model instance automatically registers it
        model = JSONModel(data_class=data_class, type_name=type_name, derived_from=derived_from, internal_type_name=internal_type_name)
        
        # Inject custom __repr__
        def _repr(self) -> str:
            return f"<{cls.__name__} (data class for JSONModel '{model.type_name}')>"
        setattr(cls, '__repr__', _repr)

        # Return the now registered dataclass
        return data_class

    return _wrapper


# Same as above, but for abstract base classes of JSON models.
@dataclass_transform(field_specifiers=(field, _json_property, json_element, json_list, json_dict))
def abstract_json_model(slots=True):
    """
    Class decorator to easily declare abstract models from their (also abstract) data classes.
    This will NOT register a JSON model, but wrap the type into dataclass.

    Parameters
    ----------
    slots : bool, default = True
        Argument passed through to dataclass constructor.
        Controls wether the dataclass should use `__slots__` for fields.

    """
    def _wrapper[T](cls : Type[T]) -> Type[T]:
        # Wrap the decorated class wrapped into a dataclass
        data_class = dataclass(cls, slots=slots)

        # Inject custom __repr__
        def _repr(self) -> str:
            return f"<{cls.__name__} (abstract data class for JSONModels)>"
        setattr(cls, '__repr__', _repr)

        # Return the dataclass
        return data_class
    
    return _wrapper
