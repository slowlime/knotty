import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.namespace_role import NamespaceRole
    from ..models.namespace_user import NamespaceUser


T = TypeVar("T", bound="Namespace")


@attr.s(auto_attribs=True)
class Namespace:
    """
    Attributes:
        name (str):
        description (str):
        created_date (datetime.datetime):
        users (List['NamespaceUser']):
        roles (List['NamespaceRole']):
        homepage (Union[Unset, str]):
    """

    name: str
    description: str
    created_date: datetime.datetime
    users: List["NamespaceUser"]
    roles: List["NamespaceRole"]
    homepage: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        description = self.description
        created_date = self.created_date.isoformat()

        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()

            users.append(users_item)

        roles = []
        for roles_item_data in self.roles:
            roles_item = roles_item_data.to_dict()

            roles.append(roles_item)

        homepage = self.homepage

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "created_date": created_date,
                "users": users,
                "roles": roles,
            }
        )
        if homepage is not UNSET:
            field_dict["homepage"] = homepage

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.namespace_role import NamespaceRole
        from ..models.namespace_user import NamespaceUser

        d = src_dict.copy()
        name = d.pop("name")

        description = d.pop("description")

        created_date = isoparse(d.pop("created_date"))

        users = []
        _users = d.pop("users")
        for users_item_data in _users:
            users_item = NamespaceUser.from_dict(users_item_data)

            users.append(users_item)

        roles = []
        _roles = d.pop("roles")
        for roles_item_data in _roles:
            roles_item = NamespaceRole.from_dict(roles_item_data)

            roles.append(roles_item)

        homepage = d.pop("homepage", UNSET)

        namespace = cls(
            name=name,
            description=description,
            created_date=created_date,
            users=users,
            roles=roles,
            homepage=homepage,
        )

        namespace.additional_properties = d
        return namespace

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
