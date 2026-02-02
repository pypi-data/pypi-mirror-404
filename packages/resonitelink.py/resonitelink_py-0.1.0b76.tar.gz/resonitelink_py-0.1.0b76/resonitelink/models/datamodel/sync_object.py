from typing import Dict

from resonitelink.models.datamodel import Member
from resonitelink.json import MISSING, json_model, json_dict


__all__ = (
    'SyncObject',
)


@json_model("syncObject", Member)
class SyncObject(Member):
    members : Dict[str, Member] = json_dict("members", Member, default=MISSING)

    def __init__(self, **members : Member):
        """
        Custom constructor to allow providing unpacked arguments for `members`.

        """
        self.members = members
