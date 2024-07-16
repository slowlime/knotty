import datetime
from typing import Any, Dict, List, Type, TypeVar, cast

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="UserInfo")


@attr.s(auto_attribs=True)
class UserInfo:
    """
    Attributes:
        username (str):
        email (str):
        registered (datetime.datetime):
        namespaces (List[str]):
    """

    username: str
    email: str
    registered: datetime.datetime
    namespaces: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        username = self.username
        email = self.email
        registered = self.registered.isoformat()

        namespaces = self.namespaces

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "email": email,
                "registered": registered,
                "namespaces": namespaces,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        username = d.pop("username")

        email = d.pop("email")

        registered = isoparse(d.pop("registered"))

        namespaces = cast(List[str], d.pop("namespaces"))

        user_info = cls(
            username=username,
            email=email,
            registered=registered,
            namespaces=namespaces,
        )

        user_info.additional_properties = d
        return user_info

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
