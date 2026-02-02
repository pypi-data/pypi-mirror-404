from dataclasses import InitVar
from typing import Optional, List

from resonitelink.models.assets.mesh.raw_data import SubmeshRawData
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'PointSubmeshRawData',
)


@json_model("points", SubmeshRawData)
class PointSubmeshRawData(SubmeshRawData):
    # How many points are in this submesh. index_count = point_count
    point_count : int = json_element("pointCount", int, default=MISSING)

    # Initializes the indices.
    init_indices : InitVar[Optional[List[int]]] = MISSING

    def __post_init__(self, init_indices : Optional[List[int]]):
        if init_indices:
            if len(init_indices) != self.index_count:
                raise ValueError(f"Expected {self.index_count} indices for {self.point_count} points, but only got {len(init_indices)} indices.")

            self.indices = init_indices

    @property
    def index_count(self) -> int:
        return self.point_count
