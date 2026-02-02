from typing import List

from resonitelink.models.assets.mesh.json import Triangle, Submesh
from resonitelink.json import MISSING, json_model, json_list


__all__ = (
    'TriangleSubmesh',
    'TriangleSubmeshFlat',
)


@json_model("triangles", Submesh)
class TriangleSubmesh(Submesh):
    """
    A submesh composed of individual triangles.
    
    """
    # All the triangles that form this submesh.
    triangles : List[Triangle] = json_list("triangles", Triangle, default=MISSING)


@json_model("trianglesFlat", Submesh)
class TriangleSubmeshFlat(Submesh):
    """
    A submesh composed of individual triangles.
    This is an alternate representation and will result in same submesh as TriangleSubmesh
    With this representation you must take care to provide the indicies for each triangle properly.
    Each triangle requires three indicies. Those indicies are consecutive.
    
    """
    # Indexes of vertices representing triangles of this mesh.
    # Note that each triangle needs three consecutive indicies in this list.
    vertex_indices : List[int] = json_list("vertexIndices", int, default=MISSING)
