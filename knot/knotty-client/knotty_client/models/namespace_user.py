import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="NamespaceUser")


@attr.s(auto_attribs=True)
class NamespaceUser:
    """
    Attributes:
        username (str):
        role (str):
        added_date (datetime.datetime):
        added_by (str):
        updated_date (datetime.datetime):
        updated_by (str):
    """

    username: str
    role: str
    added_date: datetime.datetime
    added_by: str
    updated_date: datetime.datetime
    updated_by: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        username = self.username
        role = self.role
        added_date = self.added_date.isoformat()

        added_by = self.added_by
        updated_date = self.updated_date.isoformat()

        updated_by = self.updated_by

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "role": role,
                "added_date": added_date,
                "added_by": added_by,
                "updated_date": updated_date,
                "updated_by": updated_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        username = d.pop("username")

        role = d.pop("role")

        added_date = isoparse(d.pop("added_date"))

        added_by = d.pop("added_by")

        updated_date = isoparse(d.pop("updated_date"))

        updated_by = d.pop("updated_by")

        namespace_user = cls(
            username=username,
            role=role,
            added_date=added_date,
            added_by=added_by,
            updated_date=updated_date,
            updated_by=updated_by,
        )

        namespace_user.additional_properties = d
        return namespace_user

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
