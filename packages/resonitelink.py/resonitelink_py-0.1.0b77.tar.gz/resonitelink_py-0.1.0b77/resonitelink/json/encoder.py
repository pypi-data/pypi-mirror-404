from .models import MISSING, JSONModel, JSONProperty
from typing import Any
from json import JSONEncoder


__all__ = ( 
    'ResoniteLinkJSONEncoder',
)


class ResoniteLinkJSONEncoder(JSONEncoder):
    """
    Custom encoder for ResoniteLink model classes.

    """
    def default(self, o : Any) -> Any:
        """
        Encoding logic to encode custom model structure.
        
        If the object to encode is a registered JSONModel:
        - The model's `type_name` is encoded as the `$type` argument in the resuling JSON object.
        - Only fields associated with a JSONProperty will be carried over into the resulting JSON object.
        - Fields associated with a JSONProperty will use their `name` as the key in the resulting JSON object.

        Any other object will be passed to the `default` method of the base class (`json.JSONEncoder`).
        This naturally supports encoding nested models due to how JSONEncoder is implemented.

        Parameters
        ----------
        o : Any
            The object to be encoded.
        
        Returns
        -------
        The final object to be encoded into the output JSON.

        """
        try:
            # Try retrieving a model to quickly check if the object to encode is a model's data class
            model = JSONModel.find_model(type(o))
        
        except KeyError:
            # Not a registered model class, forward to default encoder
            return super().default(o)
        
        else:
            # Object is data class of a model, resolve into object
            obj = { }
            if model.type_name:
                obj['$type'] = model.type_name

            json_property : JSONProperty
            for key, json_property in model.properties.items():
                if hasattr(o, key):
                    # Object has property for key, include
                    value = getattr(o, key)
                    if value is MISSING:
                        # Skip any properties that are set to the MISSING sentinel
                        # (This is also needed because the _MissingSentinel class can't be JSON encoded!)
                        continue

                    obj[json_property.json_name] = value
            
            return obj
