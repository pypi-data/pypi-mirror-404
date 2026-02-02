from typing import List

from resonitelink.models.assets.mesh.json import UV_Coordinate, BoneWeight
from resonitelink.models.datamodel import Float3, Color
from resonitelink.json import MISSING, json_model, json_element, json_list


__all__ = (
    'Vertex',
)


@json_model()
class Vertex():
    """
    Defines a single vertex of a mesh. Position is mandatory field, but all other properties are optional.
    
    """
    # Position of the vertex.
    position : Float3 = json_element("position", Float3, default=MISSING)
    
    # Normal vector of the vertex.
    normal : Float3 = json_element("normal", Float3, default=MISSING)

    # Tangent vector of the vertex. The 4th component indicates direction of the binormal.
    # When specifying tangent, it's strongly recommended that normals are specified too.
    tangent : Float3 = json_element("tangent", Float3, default=MISSING)
    
    # Color of the vertex.
    color : Color = json_element("color", Color, default=MISSING)
    
    # UV channel coordinates.
    # Each UV channel can have 2-4 dimensions.
    # Each vertex can have multiple UV channels.
    # The number of channels and dimensions for each MUST be same across all vertices.
    uvs : List[UV_Coordinate] = json_list("uvs", UV_Coordinate, default=MISSING)

    # Weights that define how much this vertex is affected by specific bones for skinned meshes.
    # The weights should add up to 1 across all the weights.
    bone_weights : List[BoneWeight] = json_list("boneWeights", BoneWeight, default=MISSING)
