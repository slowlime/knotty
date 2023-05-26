import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

from ..models.permission_code import PermissionCode

T = TypeVar("T", bound="NamespaceRole")


@attr.s(auto_attribs=True)
class NamespaceRole:
    """
    Attributes:
        name (str):
        permissions (List[PermissionCode]):
        created_date (datetime.datetime):
        created_by (str):
        updated_date (datetime.datetime):
        updated_by (str):
    """

    name: str
    permissions: List[PermissionCode]
    created_date: datetime.datetime
    created_by: str
    updated_date: datetime.datetime
    updated_by: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        permissions = []
        for permissions_item_data in self.permissions:
            permissions_item = permissions_item_data.value

            permissions.append(permissions_item)

        created_date = self.created_date.isoformat()

        created_by = self.created_by
        updated_date = self.updated_date.isoformat()

        updated_by = self.updated_by

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "permissions": permissions,
                "created_date": created_date,
                "created_by": created_by,
                "updated_date": updated_date,
                "updated_by": updated_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        permissions = []
        _permissions = d.pop("permissions")
        for permissions_item_data in _permissions:
            permissions_item = PermissionCode(permissions_item_data)

            permissions.append(permissions_item)

        created_date = isoparse(d.pop("created_date"))

        created_by = d.pop("created_by")

        updated_date = isoparse(d.pop("updated_date"))

        updated_by = d.pop("updated_by")

        namespace_role = cls(
            name=name,
            permissions=permissions,
            created_date=created_date,
            created_by=created_by,
            updated_date=updated_date,
            updated_by=updated_by,
        )

        namespace_role.additional_properties = d
        return namespace_role

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
