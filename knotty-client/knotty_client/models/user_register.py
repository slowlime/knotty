from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="UserRegister")


@attr.s(auto_attribs=True)
class UserRegister:
    """
    Attributes:
        username (str):
        email (str):
        password (str):
    """

    username: str
    email: str
    password: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        username = self.username
        email = self.email
        password = self.password

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "email": email,
                "password": password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        username = d.pop("username")

        email = d.pop("email")

        password = d.pop("password")

        user_register = cls(
            username=username,
            email=email,
            password=password,
        )

        user_register.additional_properties = d
        return user_register

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
