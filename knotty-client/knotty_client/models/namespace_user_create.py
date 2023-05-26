from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="NamespaceUserCreate")


@attr.s(auto_attribs=True)
class NamespaceUserCreate:
    """
    Attributes:
        username (str):
        role (str):
    """

    username: str
    role: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        username = self.username
        role = self.role

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "role": role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        username = d.pop("username")

        role = d.pop("role")

        namespace_user_create = cls(
            username=username,
            role=role,
        )

        namespace_user_create.additional_properties = d
        return namespace_user_create

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
