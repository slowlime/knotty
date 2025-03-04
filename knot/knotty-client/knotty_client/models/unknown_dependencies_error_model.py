from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="UnknownDependenciesErrorModel")


@attr.s(auto_attribs=True)
class UnknownDependenciesErrorModel:
    """
    Attributes:
        detail (str):
        packages (List[str]):
    """

    detail: str
    packages: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        detail = self.detail
        packages = self.packages

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detail": detail,
                "packages": packages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        detail = d.pop("detail")

        packages = cast(List[str], d.pop("packages"))

        unknown_dependencies_error_model = cls(
            detail=detail,
            packages=packages,
        )

        unknown_dependencies_error_model.additional_properties = d
        return unknown_dependencies_error_model

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
