from typing import List

from resonitelink.models.assets.mesh import Vertex, Submesh, Bone, Blendshape
from resonitelink.models.messages import Message
from resonitelink.json import MISSING, json_model, json_list


__all__ = (
    'ImportMeshJSON',
)


@json_model("importMeshJSON", Message)
class ImportMeshJSON(Message):
    """
    Imports a mesh asset from purely JSON definition.
    This is pretty verbose, so it's recommended only for smaller meshes, but is supported for
    convenience and ease of implementation & experimentation, at the cost of efficiency.
    If possible, it's recommended to use ImportMeshRawData for better efficiency.

    """
    # Vertices of this mesh. These are shared across sub-meshes.
    vertices : List[Vertex] = json_list("vertices", Vertex, default=MISSING)
    
    # List of submeshes (points, triangles...) representing this mesh.
    # Meshes will typically have at least one submesh.
    # Each submesh uses indicies of the vertices for its primitives.
    submeshes : List[Submesh] = json_list("submeshes", Submesh, default=MISSING)

    # Bones of the mesh when data represents a skinned mesh.
    # These will be referred to by their index from vertex data.
    bones : List[Bone] = json_list("bones", Bone, default=MISSING)

    # Blendshapes of this mesh.
    # These allow modifying the vertex positions, normals & tangents for animations such as facial expressions.
    blendshapes : List[Blendshape] = json_list("blendshapes", Blendshape, default=MISSING)
