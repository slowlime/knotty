from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.permission_code import PermissionCode

T = TypeVar("T", bound="Permission")


@attr.s(auto_attribs=True)
class Permission:
    """
    Attributes:
        code (PermissionCode): An enumeration.
        description (str):
    """

    code: PermissionCode
    description: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        code = self.code.value

        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "description": description,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        code = PermissionCode(d.pop("code"))

        description = d.pop("description")

        permission = cls(
            code=code,
            description=description,
        )

        permission.additional_properties = d
        return permission

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
