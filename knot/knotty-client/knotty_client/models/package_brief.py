import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="PackageBrief")


@attr.s(auto_attribs=True)
class PackageBrief:
    """
    Attributes:
        name (str):
        summary (str):
        labels (List[str]):
        owners (List[str]):
        updated_date (datetime.datetime):
        downloads (int):
        namespace (Union[Unset, str]):
    """

    name: str
    summary: str
    labels: List[str]
    owners: List[str]
    updated_date: datetime.datetime
    downloads: int
    namespace: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        summary = self.summary
        labels = self.labels

        owners = self.owners

        updated_date = self.updated_date.isoformat()

        downloads = self.downloads
        namespace = self.namespace

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "summary": summary,
                "labels": labels,
                "owners": owners,
                "updated_date": updated_date,
                "downloads": downloads,
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

        updated_date = isoparse(d.pop("updated_date"))

        downloads = d.pop("downloads")

        namespace = d.pop("namespace", UNSET)

        package_brief = cls(
            name=name,
            summary=summary,
            labels=labels,
            owners=owners,
            updated_date=updated_date,
            downloads=downloads,
            namespace=namespace,
        )

        package_brief.additional_properties = d
        return package_brief

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
