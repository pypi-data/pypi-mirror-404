from typing import List

from resonitelink.models.assets.mesh.json import Submesh
from resonitelink.json import MISSING, json_model, json_list


__all__ = (
    'PointSubmesh',
)


@json_model("points", Submesh)
class PointSubmesh(Submesh):
    vertex_indices : List[int] = json_list("vertexIndices", int, default=MISSING)
