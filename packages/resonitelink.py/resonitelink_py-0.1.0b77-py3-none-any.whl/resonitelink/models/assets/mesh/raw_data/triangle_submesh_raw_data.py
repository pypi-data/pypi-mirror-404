from dataclasses import InitVar
from typing import Optional, List

from resonitelink.models.assets.mesh.raw_data import SubmeshRawData
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'TriangleSubmeshRawData',
)


@json_model("triangles", SubmeshRawData)
class TriangleSubmeshRawData(SubmeshRawData):
    # How many triangles this submesh has. indices_count = triangle_count * 3.
    triangle_count : int = json_element("triangleCount", int, default=MISSING)
    
    # Initializes the indices.
    init_indices : InitVar[Optional[List[int]]] = MISSING

    def __post_init__(self, init_indices : Optional[List[int]]):
        if init_indices:
            if len(init_indices) != self.index_count:
                raise ValueError(f"Expected {self.index_count} indices for {self.triangle_count} triangles, but only got {len(init_indices)} indices.")

            self.indices = init_indices

    @property
    def index_count(self) -> int:
        return self.triangle_count * 3
