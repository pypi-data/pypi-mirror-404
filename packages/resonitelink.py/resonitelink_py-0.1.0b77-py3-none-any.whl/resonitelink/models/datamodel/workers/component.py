from typing import Type, Dict

from resonitelink.models.datamodel import Worker, Member
from resonitelink.json import MISSING, json_model, json_element, json_dict


__all__ = (
    'Component',
)


@json_model() # NOT derived from Worker, it's the same in the reference C# implementation.
class Component(Worker):
    component_type : str = json_element("componentType", str, default=MISSING)
    members : Dict[str, Member] = json_dict("members", Member, default=MISSING)

    def get_member[T : Member](self, member_type : Type[T], member_name : str) -> T:
        """
        Retrieves a member of the given type with the given name.

        Parameters
        ----------
        member_type : Type[T : Member]
            The type of the requested member. If the actual member type is incompatible, a `TypeError` will be raised.
        member_name : str
            The name of the requested member. If the component doesn't include a member with this name, a `KeyError` will be raised.

        Raises
        ------
        KeyError
            If the component doesn't include a member for `member_name`.
        TypeError
            If a member for `member_name` exists, but its type is incompatible with the requested `member_type`.

        """
        member = self.members[member_name]
        if not isinstance(member, member_type):
            raise TypeError(f"Member '{member_name}' of {self} is of type '{type(member)}', which isn't compatible with requested type {member_type}!")

        return member
