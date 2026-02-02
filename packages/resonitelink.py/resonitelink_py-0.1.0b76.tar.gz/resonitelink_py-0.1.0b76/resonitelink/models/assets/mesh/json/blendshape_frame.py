from typing import List

from resonitelink.models.datamodel import Float3
from resonitelink.json import MISSING, json_model, json_element, json_list


__all__ = (
    'BlendshapeFrame',
)


@json_model()
class BlendshapeFrame():
    # Position of the frame within the blendshape animation.
    # When blendshape has only a single frame, this should be set to 1.0.
    # With multiple frames per blendshape, this determines the position at which this set of deltas is fully applied.
    position : float = json_element("position", float, default=MISSING)

    # Delta values for vertex positions of this blendshape frame.
    # Number of deltas MUST match number of vertices.
    position_deltas : List[Float3] = json_list("positionDeltas", Float3, default=MISSING)

    # Optional. Delta values for vertex normals of this blendshape frame.
    # Number of deltas MUST match number of vertices.
    normal_deltas : List[Float3] = json_list("normalDeltas", Float3, default=MISSING)

    # Optional. Delta values for vertex tangents of this blendshape frame.
    # Number of deltas MUST match number of vertices.
    tangent_deltas : List[Float3] = json_list("tangentDeltas", Float3, default=MISSING)
