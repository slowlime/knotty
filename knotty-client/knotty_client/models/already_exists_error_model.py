from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="AlreadyExistsErrorModel")


@attr.s(auto_attribs=True)
class AlreadyExistsErrorModel:
    """
    Attributes:
        detail (str):
        what (str):
    """

    detail: str
    what: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        detail = self.detail
        what = self.what

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detail": detail,
                "what": what,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        detail = d.pop("detail")

        what = d.pop("what")

        already_exists_error_model = cls(
            detail=detail,
            what=what,
        )

        already_exists_error_model.additional_properties = d
        return already_exists_error_model

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
