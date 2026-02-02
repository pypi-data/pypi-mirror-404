from typing import List

from resonitelink.models.datamodel.member import Member
from resonitelink.json import MISSING, json_model, json_list


__all__ = (
    'SyncList',
)


@json_model("list", Member)
class SyncList(Member):
    elements : List[Member] = json_list("elements", Member, default=MISSING)

    def __init__(self, *elements : Member):
        """
        Custom constructor to allow providing unpacked arguments for `elements`.

        """
        self.elements = list(elements)
