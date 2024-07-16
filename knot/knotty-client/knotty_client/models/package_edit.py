from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="PackageEdit")


@attr.s(auto_attribs=True)
class PackageEdit:
    """
    Attributes:
        name (str):
        summary (str):
        labels (List[str]):
        owners (List[str]):
        namespace (Union[Unset, str]):
    """

    name: str
    summary: str
    labels: List[str]
    owners: List[str]
    namespace: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        summary = self.summary
        labels = self.labels

        owners = self.owners

        namespace = self.namespace

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "summary": summary,
                "labels": labels,
                "owners": owners,
            }
        )
        if namespace is not UNSET:
            field_dict["namespace"] = namespace

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        summary = d.pop("summary")

        labels = cast(List[str], d.pop("labels"))

        owners = cast(List[str], d.pop("owners"))

        namespace = d.pop("namespace", UNSET)

        package_edit = cls(
            name=name,
            summary=summary,
            labels=labels,
            owners=owners,
            namespace=namespace,
        )

        package_edit.additional_properties = d
        return package_edit

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
